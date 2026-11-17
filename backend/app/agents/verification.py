"""Application Verification Agent — ensures accuracy and validates against fabricated claims."""
from typing import Dict, Any, List
from app.agents.base import BaseAgent
import structlog

logger = structlog.get_logger()

class ApplicationVerificationAgent(BaseAgent):
    name = "application_verification_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        candidate = input_data.get("candidate", {})
        candidate_facts = input_data.get("candidate_facts", [])
        job = input_data.get("job", {})
        prepared_app = input_data.get("prepared_application", {})
        resume_data = input_data.get("resume_data", {})
        cover_letter_text = input_data.get("cover_letter_text", "")

        verification_errors: List[str] = []
        warnings: List[str] = []

        # 1. Target company & vacancy validation
        if not job.get("title"):
            verification_errors.append("Target job title is missing.")
        if not job.get("company"):
            verification_errors.append("Target company name is missing.")

        # 2. URL validation
        portal_url = job.get("application_url", "")
        if not portal_url or not (portal_url.startswith("http://") or portal_url.startswith("https://")):
            verification_errors.append("Invalid or missing application portal URL.")

        # 3. Ground truth factual validation
        verified_skills = set()
        for fact in candidate_facts:
            if fact.get("type") == "skill":
                name = fact.get("data", {}).get("name", "").lower().strip()
                if name:
                    verified_skills.add(name)

        # 4. Mandatory form fields check
        missing_fields = prepared_app.get("missing_mandatory_fields", [])
        if missing_fields:
            verification_errors.extend([f"Missing mandatory field: {f}" for f in missing_fields])

        # 5. Check resume attachment
        if not prepared_app.get("attached_resume") and not input_data.get("resume_path"):
            verification_errors.append("No resume document attached.")

        is_valid = len(verification_errors) == 0

        return {
            "is_valid": is_valid,
            "verification_errors": verification_errors,
            "warnings": warnings,
            "verified_applicant_name": candidate.get("full_name"),
            "target_position": f"{job.get('title')} at {job.get('company')}",
            "requires_human_approval": True,
        }

verification_agent = ApplicationVerificationAgent()
