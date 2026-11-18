"""
Durable SQLite Checkpointer for LangGraph.
Persists workflow checkpoints, channel values, and writes to SQLite so execution
threads survive backend restarts and support resumption, replay, and human-in-the-loop gates.
"""
import os
import json
import sqlite3
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Mapping
from contextlib import AbstractContextManager
from types import TracebackType

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)

class SqliteDurableSaver(BaseCheckpointSaver[str], AbstractContextManager):
    """
    Durable checkpointer that stores workflow states in SQLite.
    Survives application restarts and maintains historical checkpoints.
    """

    def __init__(self, db_path: Optional[str] = None):
        super().__init__()
        if not db_path:
            db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            db_path = os.path.join(db_dir, "jobpilot_local.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS langgraph_checkpoints_v2 (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    checkpoint_type TEXT NOT NULL,
                    checkpoint_blob BLOB NOT NULL,
                    metadata_type TEXT NOT NULL,
                    metadata_blob BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS langgraph_writes_v2 (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    write_type TEXT NOT NULL,
                    write_blob BLOB NOT NULL,
                    task_path TEXT,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                )
            """)
            conn.commit()

    def __enter__(self) -> "SqliteDurableSaver":
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        return False

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = str(config["configurable"]["thread_id"])
        checkpoint_ns = str(config["configurable"].get("checkpoint_ns", ""))
        checkpoint_id = config["configurable"].get("checkpoint_id")

        with self._get_connection() as conn:
            if checkpoint_id:
                cursor = conn.execute(
                    """
                    SELECT checkpoint_id, parent_checkpoint_id, checkpoint_type, checkpoint_blob, metadata_type, metadata_blob
                    FROM langgraph_checkpoints_v2
                    WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                    """,
                    (thread_id, checkpoint_ns, str(checkpoint_id)),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT checkpoint_id, parent_checkpoint_id, checkpoint_type, checkpoint_blob, metadata_type, metadata_blob
                    FROM langgraph_checkpoints_v2
                    WHERE thread_id = ? AND checkpoint_ns = ?
                    ORDER BY checkpoint_id DESC
                    LIMIT 1
                    """,
                    (thread_id, checkpoint_ns),
                )

            row = cursor.fetchone()
            if not row:
                return None

            c_id = row["checkpoint_id"]
            p_id = row["parent_checkpoint_id"]
            checkpoint_data = self.serde.loads_typed((row["checkpoint_type"], row["checkpoint_blob"]))
            metadata_data = self.serde.loads_typed((row["metadata_type"], row["metadata_blob"]))

            # Load pending writes if any
            w_cursor = conn.execute(
                """
                SELECT task_id, channel, write_type, write_blob
                FROM langgraph_writes_v2
                WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                ORDER BY idx ASC
                """,
                (thread_id, checkpoint_ns, c_id),
            )
            pending_writes = [
                (w_row["task_id"], w_row["channel"], self.serde.loads_typed((w_row["write_type"], w_row["write_blob"])))
                for w_row in w_cursor.fetchall()
            ]

            parent_config = (
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": p_id,
                    }
                }
                if p_id
                else None
            )

            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": c_id,
                    }
                },
                checkpoint=checkpoint_data,
                metadata=metadata_data,
                parent_config=parent_config,
                pending_writes=pending_writes,
            )

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        if not config:
            return

        thread_id = str(config["configurable"]["thread_id"])
        checkpoint_ns = str(config["configurable"].get("checkpoint_ns", ""))

        query = """
            SELECT checkpoint_id, parent_checkpoint_id, checkpoint_type, checkpoint_blob, metadata_type, metadata_blob
            FROM langgraph_checkpoints_v2
            WHERE thread_id = ? AND checkpoint_ns = ?
        """
        params: List[Any] = [thread_id, checkpoint_ns]

        if before and "checkpoint_id" in before.get("configurable", {}):
            query += " AND checkpoint_id < ?"
            params.append(str(before["configurable"]["checkpoint_id"]))

        query += " ORDER BY checkpoint_id DESC"
        if limit:
            query += f" LIMIT {int(limit)}"

        with self._get_connection() as conn:
            for row in conn.execute(query, params).fetchall():
                c_id = row["checkpoint_id"]
                p_id = row["parent_checkpoint_id"]
                checkpoint_data = self.serde.loads_typed((row["checkpoint_type"], row["checkpoint_blob"]))
                metadata_data = self.serde.loads_typed((row["metadata_type"], row["metadata_blob"]))

                parent_config = (
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": p_id,
                        }
                    }
                    if p_id
                    else None
                )

                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": c_id,
                        }
                    },
                    checkpoint=checkpoint_data,
                    metadata=metadata_data,
                    parent_config=parent_config,
                )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = str(config["configurable"]["thread_id"])
        checkpoint_ns = str(config["configurable"].get("checkpoint_ns", ""))
        checkpoint_id = checkpoint["id"]
        parent_id = config["configurable"].get("checkpoint_id")

        c_type, c_bytes = self.serde.dumps_typed(checkpoint)
        m_type, m_bytes = self.serde.dumps_typed(metadata)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO langgraph_checkpoints_v2
                (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, checkpoint_type, checkpoint_blob, metadata_type, metadata_blob)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (thread_id, checkpoint_ns, checkpoint_id, parent_id, c_type, c_bytes, m_type, m_bytes),
            )
            conn.commit()

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = str(config["configurable"]["thread_id"])
        checkpoint_ns = str(config["configurable"].get("checkpoint_ns", ""))
        checkpoint_id = str(config["configurable"]["checkpoint_id"])

        with self._get_connection() as conn:
            for idx, (channel, value) in enumerate(writes):
                w_type, w_bytes = self.serde.dumps_typed(value)
                conn.execute(
                    """
                    INSERT OR REPLACE INTO langgraph_writes_v2
                    (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, write_type, write_blob, task_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, w_type, w_bytes, task_path),
                )
            conn.commit()

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        return self.get_tuple(config)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        self.put_writes(config, writes, task_id, task_path)
