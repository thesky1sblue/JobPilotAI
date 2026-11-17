"""Notification Agent — creates actionable alerts for matches, approvals, and interviews."""
from datetime import datetime
from typing import Dict, Any, List
from app.agents.base import BaseAgent

class NotificationAgent(BaseAgent):
    name = "notification_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        event_type = input_data.get("event_type", "new_match")
        data = input_data.get("data", {})

        title = ""
        message = ""

        if event_type == "new_match":
            score = data.get("score", 0)
            role = data.get("title", "Position")
            company = data.get("company", "Company")
            title = f"Strong Match: {role} at {company} ({score:.0f}%)"
            message = f"JobPilot discovered a {score:.0f}% match for {role} at {company} fitting your fresher profile."

        elif event_type == "pending_approval":
            role = data.get("title", "Position")
            company = data.get("company", "Company")
            title = f"Approval Required: Application for {role} at {company}"
            message = f"Application package and tailored documents are prepared for {company}. Please review and approve submission."

        elif event_type == "interview":
            company = data.get("company", "Company")
            title = f"Interview Scheduled: {company}"
            message = f"Interview invitation detected for {company}. Check email for details."

        return {
            "title": title,
            "message": message,
            "type": event_type,
            "created_at": datetime.utcnow().isoformat(),
        }

notification_agent = NotificationAgent()
