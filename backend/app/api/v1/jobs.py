from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.jobs import Job, JobMatch, Company
from app.models.applications import Application
from typing import Optional
from datetime import datetime

router = APIRouter()

@router.get("/stats/overview")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_jobs = await db.scalar(select(func.count(Job.id))) or 0
    strong_matches = await db.scalar(select(func.count(JobMatch.id)).where(JobMatch.classification == "strong")) or 0
    today = datetime.utcnow().date()
    new_today = await db.scalar(select(func.count(Job.id)).where(func.date(Job.discovered_at) == today)) or 0
    total_apps = await db.scalar(select(func.count(Application.id))) or 0
    pending_approvals = await db.scalar(select(func.count(Application.id)).where(Application.status == "pending_approval")) or 0
    submitted = await db.scalar(select(func.count(Application.id)).where(Application.status == "submitted")) or 0
    return {
        "total_jobs_discovered": total_jobs,
        "new_today": new_today,
        "strong_matches": strong_matches,
        "applications_prepared": total_apps,
        "pending_approvals": pending_approvals,
        "applications_submitted": submitted,
    }

@router.get("/")
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
    min_score: Optional[float] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
    classification: Optional[str] = None,
    search: Optional[str] = None,
):
    q = (
        select(Job, JobMatch, Company)
        .join(Company, Job.company_id == Company.id)
        .outerjoin(JobMatch, Job.id == JobMatch.job_id)
        .where(Job.is_active == True)
    )
    if min_score is not None:
        q = q.where(JobMatch.overall_score >= min_score)
    if location:
        q = q.where(Job.location.ilike(f"%{location}%"))
    if source:
        q = q.where(Job.source == source)
    if classification:
        q = q.where(JobMatch.classification == classification)
    if search:
        q = q.where(Job.title.ilike(f"%{search}%"))
    q = q.order_by(desc(JobMatch.overall_score), desc(Job.discovered_at))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    rows = result.all()
    return {
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "jobs": [
            {
                "id": str(job.id),
                "title": job.title,
                "company": company.name,
                "location": job.location,
                "location_type": job.location_type,
                "source": job.source,
                "employment_type": job.employment_type,
                "posted_at": job.posted_at.isoformat() if job.posted_at else None,
                "discovered_at": job.discovered_at.isoformat(),
                "application_url": job.application_url,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
                "match_score": match.overall_score if match else None,
                "classification": match.classification if match else None,
            }
            for job, match, company in rows
        ],
    }

@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Job, Company, JobMatch)
        .join(Company, Job.company_id == Company.id)
        .outerjoin(JobMatch, Job.id == JobMatch.job_id)
        .where(Job.id == job_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    job, company, match = row
    return {
        "id": str(job.id),
        "title": job.title,
        "company": {"id": str(company.id), "name": company.name, "careers_url": company.careers_url},
        "description": job.description,
        "location": job.location,
        "location_type": job.location_type,
        "employment_type": job.employment_type,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "education_requirement": job.education_requirement,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "application_url": job.application_url,
        "deadline": job.deadline.isoformat() if job.deadline else None,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "match": {
            "overall_score": match.overall_score,
            "classification": match.classification,
            "matched_skills": match.matched_skills,
            "missing_skills": match.missing_skills,
            "explanation": match.explanation,
            "is_eligible": match.is_eligible,
        } if match else None,
    }

@router.post("/discover")
async def trigger_discovery(db: AsyncSession = Depends(get_db)):
    """Trigger a manual discovery run."""
    from app.services.discovery_service import run_discovery
    result = await run_discovery(db)
    return result
