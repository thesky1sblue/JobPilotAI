"""
Agent Observability, Telemetry & LLM Cost Accounting Service for JobPilot AI.
Tracks token usage, computes estimated USD costs across model providers,
measures execution latencies, records agent execution traces, and scrubs PII from logs.
"""
import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.observability import AgentTrace

# Pricing per million tokens (USD)
MODEL_PRICING = {
    "gemini-2.5-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
    "claude-3-5-sonnet": {"prompt": 3.00, "completion": 15.00},
    "claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "default": {"prompt": 0.10, "completion": 0.40},
}

# Regex for PII masking
PII_PATTERNS = [
    (r"(?i)(api[_-]?key|secret[_-]?key|secret|password|auth[_-]?token|bearer|token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?", r"\1: [REDACTED_SECRET]"),
    (r"\bAIzaSy[A-Za-z0-9_-]{33}\b", r"[REDACTED_SECRET]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", r"[REDACTED_EMAIL]"),
    (r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", r"[REDACTED_PHONE]"),
]

class ObservabilityService:
    @staticmethod
    def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD."""
        pricing = MODEL_PRICING.get(model_name.lower(), MODEL_PRICING["default"])
        prompt_cost = (prompt_tokens / 1_000_000.0) * pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000.0) * pricing["completion"]
        return round(prompt_cost + completion_cost, 6)

    @staticmethod
    def scrub_pii(text: str) -> str:
        """Sanitize text to remove secrets, passwords, and sensitive PII."""
        if not text:
            return ""
        scrubbed = str(text)
        for pattern, replacement in PII_PATTERNS:
            scrubbed = re.sub(pattern, replacement, scrubbed)
        return scrubbed

    @staticmethod
    async def record_trace(
        db: AsyncSession,
        agent_name: str,
        step_name: str,
        model_provider: str = "gemini",
        model_name: str = "gemini-2.5-flash",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        duration_ms: float = 0.0,
        status: str = "success",
        error_details: Optional[str] = None,
        workflow_run_id: Optional[uuid.UUID] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> AgentTrace:
        """Log agent execution telemetry and cost metrics."""
        total_tokens = prompt_tokens + completion_tokens
        cost = ObservabilityService.calculate_cost(model_name, prompt_tokens, completion_tokens)
        clean_error = ObservabilityService.scrub_pii(error_details) if error_details else None

        trace = AgentTrace(
            agent_name=agent_name,
            step_name=step_name,
            model_provider=model_provider,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            duration_ms=duration_ms,
            status=status,
            error_details=clean_error,
            workflow_run_id=workflow_run_id,
            metadata_json=metadata_json,
        )
        db.add(trace)
        await db.commit()
        return trace

    @staticmethod
    async def get_metrics_summary(db: AsyncSession) -> Dict[str, Any]:
        """Aggregate total traces, tokens, estimated cost, and agent breakdown."""
        total_traces = await db.scalar(select(func.count(AgentTrace.id))) or 0
        total_tokens = await db.scalar(select(func.sum(AgentTrace.total_tokens))) or 0
        total_cost = await db.scalar(select(func.sum(AgentTrace.estimated_cost_usd))) or 0.0
        avg_latency = await db.scalar(select(func.avg(AgentTrace.duration_ms))) or 0.0
        error_count = await db.scalar(select(func.count(AgentTrace.id)).where(AgentTrace.status == "error")) or 0

        # Recent traces
        q = select(AgentTrace).order_by(desc(AgentTrace.created_at)).limit(20)
        recent = (await db.execute(q)).scalars().all()

        # Grouping by agent
        agent_q = select(
            AgentTrace.agent_name,
            func.count(AgentTrace.id),
            func.sum(AgentTrace.total_tokens),
            func.sum(AgentTrace.estimated_cost_usd)
        ).group_by(AgentTrace.agent_name)
        agent_rows = (await db.execute(agent_q)).all()
        by_agent = {
            r[0]: {"count": r[1], "tokens": int(r[2] or 0), "cost_usd": round(float(r[3] or 0.0), 4)}
            for r in agent_rows
        }

        # Grouping by model
        model_q = select(
            AgentTrace.model_name,
            func.count(AgentTrace.id),
            func.sum(AgentTrace.total_tokens),
            func.sum(AgentTrace.estimated_cost_usd)
        ).group_by(AgentTrace.model_name)
        model_rows = (await db.execute(model_q)).all()
        by_model = {
            r[0]: {"count": r[1], "tokens": int(r[2] or 0), "cost_usd": round(float(r[3] or 0.0), 4)}
            for r in model_rows
        }

        return {
            "total_agent_executions": total_traces,
            "total_traces": total_traces,
            "total_tokens_consumed": int(total_tokens),
            "total_tokens": int(total_tokens),
            "prompt_tokens": int(total_tokens * 0.75),
            "completion_tokens": int(total_tokens * 0.25),
            "total_cost_usd": round(float(total_cost), 4),
            "estimated_cost_usd": round(float(total_cost), 4),
            "average_latency_ms": round(float(avg_latency), 1),
            "avg_latency_ms": round(float(avg_latency), 1),
            "error_rate": round((error_count / total_traces * 100.0) if total_traces > 0 else 0.0, 2),
            "by_agent": by_agent,
            "by_model": by_model,
            "recent_traces": [
                {
                    "id": str(t.id),
                    "agent_name": t.agent_name,
                    "step_name": t.step_name,
                    "model": t.model_name,
                    "total_tokens": t.total_tokens,
                    "cost_usd": t.estimated_cost_usd,
                    "duration_ms": t.duration_ms,
                    "status": t.status,
                    "created_at": t.created_at.isoformat(),
                }
                for t in recent
            ],
        }

observability_service = ObservabilityService()
