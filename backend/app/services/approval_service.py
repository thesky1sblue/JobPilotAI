"""
Human Approval Service for JobPilot AI.
Enforces strict cryptographic payload hashing and human-in-the-loop validation.
Ensures that no application can be submitted without explicit human approval and
that any change to application content immediately invalidates prior approvals.
"""
import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

class ApprovalService:
    @staticmethod
    def compute_payload_hash(
        applicant_data: Dict[str, Any],
        job_data: Dict[str, Any],
        answers: Dict[str, Any],
        resume_identifier: str = "",
        cover_letter_identifier: str = "",
    ) -> str:
        """
        Compute SHA-256 hash of all material application content.
        Any modification to answers, job details, or attached documents alters this hash.
        """
        canonical_dict = {
            "applicant": {
                "name": applicant_data.get("full_name"),
                "email": applicant_data.get("email"),
                "phone": applicant_data.get("phone"),
                "linkedin": applicant_data.get("linkedin_url"),
                "github": applicant_data.get("github_url"),
            },
            "job": {
                "title": job_data.get("title"),
                "company": job_data.get("company"),
                "url": job_data.get("application_url"),
            },
            "answers": sorted(answers.items()),
            "resume": resume_identifier,
            "cover_letter": cover_letter_identifier,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_approval_integrity(
        current_payload_hash: str,
        approved_payload_hash: Optional[str],
        approval_status: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates that the application has been explicitly approved AND
        that the payload has not mutated since approval was granted.
        """
        if approval_status != "approved":
            return False, f"Application status is '{approval_status}', not 'approved'."

        if not approved_payload_hash:
            return False, "No approved payload hash found on record."

        if current_payload_hash != approved_payload_hash:
            return False, "Payload mutation detected: application contents changed after approval was granted. Re-approval required."

        return True, None

approval_service = ApprovalService()
