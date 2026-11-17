"""Application Tracking Agent — monitors application lifecycle, prevents duplicates, and records stages."""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.agents.base import BaseAgent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.applications import Application, ApplicationEvent

VALID_STATUSES = [
    "discovered",
    "shortlisted",
    "preparing",
    "pending_approval",
    "approved",
    "submitted",
    "assessment",
    "interview",
    "rejected",
    "offer",
    "withdrawn",
]

class ApplicationTrackingAgent(BaseAgent):
    name = "application_tracking_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        action = input_data.get("action", "check_duplicate")
        job_id = input_data.get("job_id")
        candidate_id = input_data.get("candidate_id")

        if action == "check_duplicate":
            existing = input_data.get("existing_applications", [])
            is_duplicate = any(str(app.get("job_id")) == str(job_id) for app in existing)
            return {
                "is_duplicate": is_duplicate,
                "can_apply": not is_duplicate,
                "reason": "Application already exists for this job vacancy" if is_duplicate else "Eligible for new application",
            }

        elif action == "record_stage":
            new_status = input_data.get("new_status")
            if new_status not in VALID_STATUSES:
                raise ValueError(f"Invalid status: {new_status}")
            return {
                "application_id": input_data.get("application_id"),
                "status": new_status,
                "timestamp": datetime.utcnow().isoformat(),
                "notes": input_data.get("notes", ""),
            }

        return {"status": "ok"}

tracking_agent = ApplicationTrackingAgent()
