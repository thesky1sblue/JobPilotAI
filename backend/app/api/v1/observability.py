import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.observability import AgentTrace
from app.services.observability_service import observability_service

router = APIRouter()

@router.get("/metrics")
async def get_observability_metrics(db: AsyncSession = Depends(get_db)):
    """Aggregate agent executions, token consumption, and estimated LLM costs."""
    return await observability_service.get_metrics_summary(db)

@router.get("/traces")
async def list_agent_traces(
    limit: int = Query(50, ge=1, le=200),
    agent_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed agent execution traces with duration and costs."""
    q = select(AgentTrace).order_by(desc(AgentTrace.created_at)).limit(limit)
    if agent_name:
        q = q.where(AgentTrace.agent_name == agent_name)

    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(t.id),
            "agent_name": t.agent_name,
            "step_name": t.step_name,
            "model_provider": t.model_provider,
            "model_name": t.model_name,
            "prompt_tokens": t.prompt_tokens,
            "completion_tokens": t.completion_tokens,
            "total_tokens": t.total_tokens,
            "estimated_cost_usd": t.estimated_cost_usd,
            "duration_ms": t.duration_ms,
            "status": t.status,
            "error_details": t.error_details,
            "created_at": t.created_at.isoformat(),
        }
        for t in rows
    ]
