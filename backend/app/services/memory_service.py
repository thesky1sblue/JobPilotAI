"""
Persistent Memory Service for JobPilot AI.
Maintains candidate ground truth, learned company ATS quirks, and workflow recovery states.
"""
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.memory import CompanyMemory
from app.models.jobs import Company
from app.models.candidate import CandidateProfile, CandidateFact

class MemoryService:
    @staticmethod
    async def get_or_create_company_memory(db: AsyncSession, company_id: uuid.UUID, ats_type: str = "custom") -> CompanyMemory:
        result = await db.execute(select(CompanyMemory).where(CompanyMemory.company_id == company_id))
        mem = result.scalar_one_or_none()
        if not mem:
            mem = CompanyMemory(
                company_id=company_id,
                ats_type=ats_type,
                known_questions=[],
                portal_quirks={},
                automation_success_count=0,
                automation_failure_count=0,
                anti_bot_observed=False,
            )
            db.add(mem)
            await db.flush()
        return mem

    @staticmethod
    async def record_automation_outcome(
        db: AsyncSession,
        company_id: uuid.UUID,
        success: bool,
        anti_bot: bool = False,
        discovered_questions: Optional[List[str]] = None,
        quirks: Optional[Dict[str, Any]] = None,
    ) -> None:
        mem = await MemoryService.get_or_create_company_memory(db, company_id)
        if success:
            mem.automation_success_count += 1
        else:
            mem.automation_failure_count += 1

        if anti_bot:
            mem.anti_bot_observed = True

        if discovered_questions:
            existing = set(mem.known_questions or [])
            existing.update(discovered_questions)
            mem.known_questions = list(existing)

        if quirks:
            current_quirks = dict(mem.portal_quirks or {})
            current_quirks.update(quirks)
            mem.portal_quirks = current_quirks

        await db.commit()

    @staticmethod
    async def get_candidate_ground_truth(db: AsyncSession, candidate_id: uuid.UUID) -> Dict[str, Any]:
        """Fetch strictly verified candidate facts without unverified claims."""
        cand_res = await db.execute(select(CandidateProfile).where(CandidateProfile.id == candidate_id))
        candidate = cand_res.scalar_one_or_none()
        if not candidate:
            return {}

        facts_res = await db.execute(
            select(CandidateFact)
            .where(CandidateFact.candidate_id == candidate_id, CandidateFact.verified == True)
        )
        verified_facts = [{"type": f.fact_type, "data": f.fact_data} for f in facts_res.scalars().all()]

        return {
            "profile": {
                "id": str(candidate.id),
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "location": candidate.location,
                "linkedin_url": candidate.linkedin_url,
                "github_url": candidate.github_url,
                "portfolio_url": candidate.portfolio_url,
                "experience_years": candidate.experience_years,
            },
            "facts": verified_facts,
        }

memory_service = MemoryService()
