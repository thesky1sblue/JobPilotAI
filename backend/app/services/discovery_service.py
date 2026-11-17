"""Discovery service: runs connectors and saves jobs."""
import asyncio
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.jobs import Company, Job, JobMatch
from app.models.candidate import CandidateProfile, CandidateFact, JobPreference
from app.connectors.greenhouse import GreenhouseConnector
from app.connectors.lever import LeverConnector
from app.agents.extraction import ExtractionAgent
from app.agents.matching import MatchingAgent
from datetime import datetime
from typing import List, Dict, Any, Tuple

logger = structlog.get_logger()
extractor = ExtractionAgent()
matcher = MatchingAgent()

async def fetch_company_jobs(company: Company, gh: GreenhouseConnector, lv: LeverConnector, sem: asyncio.Semaphore) -> Tuple[Company, List[Dict[str, Any]], str]:
    if not company.ats_identifier:
        return (company, [], "")
    async with sem:
        try:
            if company.ats_platform == "greenhouse":
                jobs = await gh.fetch_all_for_company(company.ats_identifier)
                return (company, jobs, "")
            elif company.ats_platform == "lever":
                jobs = await lv.fetch_all_for_company(company.ats_identifier)
                return (company, jobs, "")
            return (company, [], "")
        except Exception as e:
            return (company, [], str(e))

async def run_discovery(db: AsyncSession) -> dict:
    """Run discovery concurrently for all watchlisted companies."""
    result = await db.execute(
        select(Company).where(Company.is_in_watchlist == True, Company.ats_platform.in_(["greenhouse", "lever"]))
    )
    companies = result.scalars().all()
    
    candidate_result = await db.execute(select(CandidateProfile).limit(1))
    candidate = candidate_result.scalar_one_or_none()
    candidate_facts = []
    preferences = {}
    
    if candidate:
        facts_result = await db.execute(select(CandidateFact).where(CandidateFact.candidate_id == candidate.id))
        candidate_facts = [{"type": f.fact_type, "data": f.fact_data} for f in facts_result.scalars().all()]
        pref_result = await db.execute(select(JobPreference).where(JobPreference.candidate_id == candidate.id))
        pref = pref_result.scalar_one_or_none()
        if pref:
            preferences = {
                "target_roles": pref.target_roles,
                "preferred_locations": pref.preferred_locations,
                "experience_years": pref.experience_years,
            }
        else:
            preferences = {"preferred_locations": ["Bangalore", "Remote", "Chennai", "Hyderabad"], "experience_years": 0}
    
    gh = GreenhouseConnector()
    lv = LeverConnector()
    sem = asyncio.Semaphore(10)
    
    tasks = [fetch_company_jobs(c, gh, lv, sem) for c in companies]
    results = await asyncio.gather(*tasks)
    
    total_new = 0
    errors = []
    
    for company, raw_jobs, err in results:
        if err:
            errors.append({"company": company.name, "error": err})
            continue
            
        company.last_discovered_at = datetime.utcnow()
        for raw in raw_jobs:
            # Check duplicate
            existing = await db.execute(
                select(Job).where(Job.source == raw["source"], Job.source_id == str(raw["source_id"]))
            )
            if existing.scalar_one_or_none():
                continue
            
            # Extract
            ex_result = await extractor.run({"raw_job": raw})
            if ex_result["status"] != "success":
                continue
            extracted = ex_result["data"]
            
            # Save job
            job = Job(
                company_id=company.id,
                source=extracted["source"],
                source_id=str(extracted["source_id"]),
                title=extracted["title"],
                description=extracted.get("description"),
                location=extracted.get("location"),
                location_type=extracted.get("location_type"),
                department=extracted.get("department"),
                required_skills=extracted.get("required_skills"),
                application_url=extracted.get("application_url"),
                raw_payload=extracted.get("raw_payload"),
                posted_at=None,
            )
            db.add(job)
            await db.flush()
            
            # Match if candidate exists
            if candidate:
                match_result = await matcher.run({
                    "job": {
                        "id": str(job.id),
                        "title": job.title,
                        "required_skills": job.required_skills,
                        "location": job.location,
                        "experience_min": job.experience_min,
                    },
                    "candidate_facts": candidate_facts,
                    "preferences": preferences,
                })
                if match_result["status"] == "success":
                    md = match_result["data"]
                    match = JobMatch(
                        job_id=job.id,
                        candidate_id=candidate.id,
                        overall_score=md["overall_score"],
                        skill_score=md["skill_score"],
                        role_score=md["role_score"],
                        experience_score=md["experience_score"],
                        location_score=md["location_score"],
                        salary_score=md["salary_score"],
                        education_score=md["education_score"],
                        matched_skills=md["matched_skills"],
                        missing_skills=md["missing_skills"],
                        explanation=md["explanation"],
                        is_eligible=md["is_eligible"],
                        classification=md["classification"],
                    )
                    db.add(match)
            
            total_new += 1
            
    await db.commit()
    return {"new_jobs": total_new, "companies_scanned": len(companies), "errors": errors}
