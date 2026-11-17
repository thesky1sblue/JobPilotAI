"""Application Preparation Agent — uses Playwright to inspect & populate application forms."""
import asyncio
from typing import Dict, Any, List, Optional
import structlog
from app.agents.base import BaseAgent

logger = structlog.get_logger()

# Standard field name mappings across Greenhouse, Lever, and standard ATS portals
FIELD_MAPPINGS = {
    "first_name": ["first_name", "first-name", "firstname", "fname", "given_name"],
    "last_name": ["last_name", "last-name", "lastname", "lname", "family_name"],
    "full_name": ["name", "full_name", "candidate_name", "applicant_name"],
    "email": ["email", "email_address", "applicant_email"],
    "phone": ["phone", "phone_number", "telephone", "mobile"],
    "linkedin": ["linkedin", "linkedin_url", "linkedin_profile"],
    "github": ["github", "github_url", "github_profile"],
    "portfolio": ["portfolio", "website", "personal_website"],
    "location": ["location", "city", "address"],
}

class ApplicationPreparationAgent(BaseAgent):
    name = "application_preparation_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspect the target application form, map fields to verified candidate information,
        stage answers, and produce a structured pre-submission package.
        """
        portal_url = input_data.get("portal_url", "")
        candidate = input_data.get("candidate", {})
        candidate_facts = input_data.get("candidate_facts", [])
        resume_path = input_data.get("resume_path", "")

        mapped_fields: Dict[str, Any] = {}
        missing_mandatory_fields: List[str] = []

        # Map candidate personal information
        name_parts = candidate.get("full_name", "").split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        prepared_values = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": candidate.get("full_name", ""),
            "email": candidate.get("email", ""),
            "phone": candidate.get("phone", ""),
            "linkedin": candidate.get("linkedin_url", ""),
            "github": candidate.get("github_url", ""),
            "portfolio": candidate.get("portfolio_url", ""),
            "location": candidate.get("location", ""),
        }

        # Check required fields
        if not prepared_values["full_name"]:
            missing_mandatory_fields.append("full_name")
        if not prepared_values["email"]:
            missing_mandatory_fields.append("email")
        if not resume_path:
            missing_mandatory_fields.append("resume_file")

        # Detect ATS platform from URL
        portal_type = "manual"
        if "greenhouse.io" in portal_url or "boards.greenhouse.io" in portal_url:
            portal_type = "greenhouse"
        elif "lever.co" in portal_url:
            portal_type = "lever"
        elif "workday.com" in portal_url or "myworkdayjobs.com" in portal_url:
            portal_type = "workday"

        review_summary = {
            "portal_url": portal_url,
            "portal_type": portal_type,
            "applicant": {
                "name": candidate.get("full_name"),
                "email": candidate.get("email"),
                "phone": candidate.get("phone"),
                "linkedin": candidate.get("linkedin_url"),
                "github": candidate.get("github_url"),
            },
            "attached_resume": resume_path,
            "staged_answers": prepared_values,
            "missing_fields": missing_mandatory_fields,
            "is_ready_for_review": len(missing_mandatory_fields) == 0,
        }

        return {
            "portal_type": portal_type,
            "review_summary": review_summary,
            "prepared_answers": prepared_values,
            "missing_mandatory_fields": missing_mandatory_fields,
            "is_ready": len(missing_mandatory_fields) == 0,
        }

application_prep_agent = ApplicationPreparationAgent()
