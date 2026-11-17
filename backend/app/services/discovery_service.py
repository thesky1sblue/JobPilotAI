"""Discovery service: runs connectors and saves jobs."""
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

logger = structlog.get_logger()
extractor = ExtractionAgent()
matcher = MatchingAgent()

async def run_discovery(db: AsyncSession) -> dict:
    """Run discovery for all watchlisted companies."""
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
    
    total_new = 0
    errors = []
    
    for company in companies:
        if not company.ats_identifier:
            continue
        try:
            if company.ats_platform == "greenhouse":
                raw_jobs = await gh.fetch_all_for_company(company.ats_identifier)
            elif company.ats_platform == "lever":
                raw_jobs = await lv.fetch_all_for_company(company.ats_identifier)
            else:
                continue
            
            for raw in raw_jobs:
                # Check duplicate
                existing = await db.execute(
                    select(Job).where(Job.source == raw["source"], Job.source_id == raw["source_id"])
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
                    source_id=extracted["source_id"],
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
            
            company.last_discovered_at = datetime.utcnow()
            await db.commit()
            
        except Exception as e:
            logger.error("discovery.company_error", company=company.name, error=str(e))
            errors.append({"company": company.name, "error": str(e)})
    
    return {"new_jobs": total_new, "companies_scanned": len(companies), "errors": errors}
