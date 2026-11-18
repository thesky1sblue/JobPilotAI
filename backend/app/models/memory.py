import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, DateTime, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class CompanyMemory(Base):
    __tablename__ = "company_memories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), unique=True)
    ats_type: Mapped[str] = mapped_column(String(50), default="custom")
    portal_quirks: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # custom field patterns, required fields
    known_questions: Mapped[Optional[list]] = mapped_column(JSONB, default=list)  # recurring form questions
    automation_success_count: Mapped[int] = mapped_column(Integer, default=0)
    automation_failure_count: Mapped[int] = mapped_column(Integer, default=0)
    anti_bot_observed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WorkflowCheckpointRecord(Base):
    __tablename__ = "workflow_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[str] = mapped_column(String(255), index=True)
    checkpoint_ns: Mapped[str] = mapped_column(String(255), default="")
    checkpoint_id: Mapped[str] = mapped_column(String(255), index=True)
    parent_checkpoint_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    step_name: Mapped[str] = mapped_column(String(100), default="checkpoint")
    state_payload: Mapped[dict] = mapped_column(JSONB)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
