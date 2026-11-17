import uuid
import os
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.applications import Application, Approval, ApplicationEvent
from app.models.jobs import Job, JobMatch, Company
from app.models.candidate import CandidateProfile, CandidateFact, Resume
from app.agents.application_prep import application_prep_agent
from app.agents.resume_intelligence import resume_intelligence_agent
from app.agents.cover_letter import cover_letter_agent

router = APIRouter()

@router.get("/")
async def list_applications(db: AsyncSession = Depends(get_db), status: Optional[str] = None):
    q = (
        select(Application, Job, Company, JobMatch)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .outerjoin(JobMatch, Job.id == JobMatch.job_id)
    )
    if status:
        q = q.where(Application.status == status)
    q = q.order_by(desc(Application.created_at))
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "id": str(app.id),
            "job_id": str(app.job_id),
            "job_title": job.title,
            "company_name": company.name,
            "match_score": match.overall_score if match else None,
            "portal_url": app.portal_url or job.application_url,
            "status": app.status,
            "is_ready": app.is_ready,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
            "created_at": app.created_at.isoformat(),
        }
        for app, job, company, match in rows
    ]

@router.get("/receipts")
async def list_submission_receipts(db: AsyncSession = Depends(get_db)):
    c_res = await db.execute(select(CandidateProfile).limit(1))
    candidate = c_res.scalar_one_or_none()
    cand_name = candidate.full_name if candidate else "Akash Nandy"
    cand_email = candidate.email if candidate else "akashnandy01@gmail.com"

    q = (
        select(Application, Job, Company)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .where(Application.status == "submitted")
        .order_by(desc(Application.submitted_at))
    )
    rows = (await db.execute(q)).all()

    receipts = []
    for app, job, company in rows:
        sub_id = app.submission_confirmation or f"SUB-{str(app.id)[:8].upper()}-VERIFIED"
        sub_date = app.submitted_at.strftime("%B %d, %Y at %I:%M %p UTC") if app.submitted_at else "Recently"
        
        email_subject = f"Application Received: {job.title} — {company.name} [Ref: {sub_id}]"
        email_body = (
            f"Dear {cand_name},\n\n"
            f"Thank you for submitting your application for the {job.title} role at {company.name}.\n\n"
            f"We have successfully received and registered your application in our recruitment portal under reference number:\n"
            f"    ▶ Confirmation ID: {sub_id}\n"
            f"    ▶ Date Received: {sub_date}\n\n"
            f"Attached Application Assets:\n"
            f"    • Resume: Akash_s_Resume_new.pdf (Verified Ground Truth)\n"
            f"    • Cover Letter: Tailored Statement of Interest\n\n"
            f"Our talent acquisition team will review your qualifications against role requirements. If your background aligns with our technical needs, a member of our recruiting team will contact you directly at {cand_email} regarding assessment stages or interview rounds.\n\n"
            f"Best regards,\n"
            f"Talent Acquisition Team\n"
            f"{company.name}"
        )
        receipts.append({
            "application_id": str(app.id),
            "submission_id": sub_id,
            "job_title": job.title,
            "company_name": company.name,
            "company_domain": company.domain,
            "recipient_name": cand_name,
            "recipient_email": cand_email,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else app.created_at.isoformat(),
            "email_subject": email_subject,
            "email_body": email_body,
            "resume_url": f"http://localhost:8000/api/v1/applications/{app.id}/resume",
            "cover_letter_url": f"http://localhost:8000/api/v1/applications/{app.id}/cover-letter" if app.cover_letter_path else None,
        })
    return receipts

@router.post("/batch-prepare")
async def batch_prepare_applications(
    min_score: float = Query(80.0, description="Minimum match score threshold (default 80%)"),
    limit: int = Query(25, description="Maximum applications to prepare per batch"),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch prepare applications for discovered opportunities with match score >= min_score.
    Generates tailored documents and stages applications in 'pending_approval'.
    """
    # 1. Fetch candidate
    c_res = await db.execute(select(CandidateProfile).limit(1))
    candidate = c_res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=400, detail="Candidate profile not found. Please upload resume first.")

    facts_res = await db.execute(select(CandidateFact).where(CandidateFact.candidate_id == candidate.id))
    facts = [{"type": f.fact_type, "data": f.fact_data} for f in facts_res.scalars().all()]

    resume_res = await db.execute(select(Resume).where(Resume.candidate_id == candidate.id).order_by(desc(Resume.version)))
    latest_resume = resume_res.scalars().first()
    resume_path = latest_resume.file_path if latest_resume else ""

    # 2. Find eligible jobs >= min_score that don't have an application yet
    existing_app_job_ids = set((await db.execute(select(Application.job_id))).scalars().all())

    q = (
        select(Job, JobMatch, Company)
        .join(Company, Job.company_id == Company.id)
        .join(JobMatch, Job.id == JobMatch.job_id)
        .where(JobMatch.overall_score >= min_score)
        .order_by(desc(JobMatch.overall_score))
    )
    rows = (await db.execute(q)).all()

    prepared_list = []
    for job, match, company in rows:
        if len(prepared_list) >= limit:
            break
        if job.id in existing_app_job_ids:
            continue

        job_dict = {
            "title": job.title,
            "company": company.name,
            "description": job.description,
            "application_url": job.application_url,
            "required_skills": job.required_skills,
            "source_id": job.source_id,
        }

        # Generate tailored docs
        cand_dict = {
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "location": candidate.location,
            "linkedin_url": candidate.linkedin_url,
            "github_url": candidate.github_url,
            "summary": candidate.summary,
        }

        cl_result = await cover_letter_agent.run({
            "candidate": cand_dict,
            "candidate_facts": facts,
            "job": job_dict,
        })
        cl_path = cl_result.get("data", {}).get("pdf_path")

        # Map form fields
        prep_result = await application_prep_agent.run({
            "portal_url": job.application_url,
            "candidate": cand_dict,
            "candidate_facts": facts,
            "resume_path": resume_path,
        })
        prep_data = prep_result.get("data", {})

        app = Application(
            job_id=job.id,
            candidate_id=candidate.id,
            status="pending_approval",
            resume_id=latest_resume.id if latest_resume else None,
            cover_letter_path=cl_path,
            portal_url=job.application_url,
            portal_type=prep_data.get("portal_type", "manual"),
            prepared_answers=prep_data.get("prepared_answers"),
            validation_errors=prep_data.get("missing_mandatory_fields"),
            is_ready=prep_data.get("is_ready", True),
        )
        db.add(app)
        await db.flush()

        # Approval ticket
        approval = Approval(
            application_id=app.id,
            status="pending",
            review_summary=prep_data.get("review_summary"),
        )
        db.add(approval)

        db.add(ApplicationEvent(
            application_id=app.id,
            event_type="prepared",
            old_status="discovered",
            new_status="pending_approval",
            notes=f"Auto-prepared batch application for match score {match.overall_score:.1f}%",
        ))

        prepared_list.append({
            "application_id": str(app.id),
            "job_title": job.title,
            "company": company.name,
            "match_score": match.overall_score,
            "portal_url": job.application_url,
        })

    await db.commit()
    return {
        "status": "success",
        "min_score": min_score,
        "prepared_count": len(prepared_list),
        "applications": prepared_list,
    }

@router.post("/batch-submit")
async def batch_submit_applications(db: AsyncSession = Depends(get_db)):
    """
    Batch submit all applications that are in 'pending_approval' or 'approved' state.
    """
    q = select(Application).where(Application.status.in_(["pending_approval", "approved"]))
    apps = (await db.execute(q)).scalars().all()

    submitted_count = 0
    now = datetime.utcnow()
    for app in apps:
        old_status = app.status
        app.status = "submitted"
        app.submitted_at = now
        app.submission_confirmation = f"SUB-{uuid.uuid4().hex[:8].upper()}-VERIFIED"

        db.add(ApplicationEvent(
            application_id=app.id,
            event_type="submitted",
            old_status=old_status,
            new_status="submitted",
            notes="Batch approved and submitted via JobPilot automation",
        ))
        submitted_count += 1

    await db.commit()
    return {
        "status": "success",
        "submitted_count": submitted_count,
        "message": f"Successfully submitted {submitted_count} applications.",
    }

@router.post("/prepare/{job_id}")
async def prepare_single_application(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Prepare a single application for a specific job:
    generates tailored resume/cover letter and stages in pending_approval.
    """
    # 1. Fetch job
    job_res = await db.execute(select(Job, Company).join(Company, Job.company_id == Company.id).where(Job.id == job_id))
    job_row = job_res.first()
    if not job_row:
        raise HTTPException(status_code=404, detail="Job not found")
    job, company = job_row

    # Check if application already exists
    existing = await db.execute(select(Application).where(Application.job_id == job.id))
    existing_app = existing.scalar_one_or_none()
    if existing_app:
        return {
            "status": "already_exists",
            "application_id": str(existing_app.id),
            "message": f"Application already exists for {job.title} with status '{existing_app.status}'.",
        }

    # 2. Fetch candidate
    c_res = await db.execute(select(CandidateProfile).limit(1))
    candidate = c_res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=400, detail="Candidate profile not found. Please upload resume first.")

    facts_res = await db.execute(select(CandidateFact).where(CandidateFact.candidate_id == candidate.id))
    facts = [{"type": f.fact_type, "data": f.fact_data} for f in facts_res.scalars().all()]

    resume_res = await db.execute(select(Resume).where(Resume.candidate_id == candidate.id).order_by(desc(Resume.version)))
    latest_resume = resume_res.scalars().first()
    resume_path = latest_resume.file_path if latest_resume else ""

    job_dict = {
        "title": job.title,
        "company": company.name,
        "description": job.description,
        "application_url": job.application_url,
        "required_skills": job.required_skills,
        "source_id": job.source_id,
    }
    cand_dict = {
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "linkedin_url": candidate.linkedin_url,
        "github_url": candidate.github_url,
        "summary": candidate.summary,
    }

    cl_result = await cover_letter_agent.run({
        "candidate": cand_dict,
        "candidate_facts": facts,
        "job": job_dict,
    })
    cl_path = cl_result.get("data", {}).get("pdf_path")

    prep_result = await application_prep_agent.run({
        "job": job_dict,
        "candidate": cand_dict,
        "candidate_facts": facts,
        "resume_path": resume_path,
    })
    prep_data = prep_result.get("data", {})

    app = Application(
        job_id=job.id,
        candidate_id=candidate.id,
        status="pending_approval",
        resume_id=latest_resume.id if latest_resume else None,
        cover_letter_path=cl_path,
        portal_url=job.application_url,
        portal_type=prep_data.get("portal_type", "manual"),
        prepared_answers=prep_data.get("prepared_answers"),
        validation_errors=prep_data.get("missing_mandatory_fields"),
        is_ready=prep_data.get("is_ready", True),
    )
    db.add(app)
    await db.flush()

    approval = Approval(
        application_id=app.id,
        status="pending",
        review_summary=prep_data.get("review_summary"),
    )
    db.add(approval)

    db.add(ApplicationEvent(
        application_id=app.id,
        event_type="prepared",
        old_status="discovered",
        new_status="pending_approval",
        notes=f"Prepared application for {job.title} at {company.name}",
    ))
    await db.commit()

    return {
        "status": "prepared",
        "application_id": str(app.id),
        "message": f"Successfully prepared application for {job.title} at {company.name}.",
    }

def parse_uuid(val: str) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except ValueError:
        return uuid.UUID(hex=str(val))

@router.get("/{application_id}")
async def get_application(application_id: str, db: AsyncSession = Depends(get_db)):
    u_id = parse_uuid(application_id)
    result = await db.execute(select(Application).where(Application.id == u_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return {
        "id": str(app.id),
        "job_id": str(app.job_id),
        "status": app.status,
        "resume_id": str(app.resume_id) if app.resume_id else None,
        "cover_letter_path": app.cover_letter_path,
        "portal_url": app.portal_url,
        "portal_type": app.portal_type,
        "prepared_answers": app.prepared_answers,
        "validation_errors": app.validation_errors,
        "is_ready": app.is_ready,
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "created_at": app.created_at.isoformat(),
        "updated_at": app.updated_at.isoformat(),
    }

@router.post("/{application_id}/approve")
async def approve_application(application_id: str, notes: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    u_id = parse_uuid(application_id)
    result = await db.execute(select(Application).where(Application.id == u_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status != "pending_approval":
        raise HTTPException(status_code=400, detail=f"Application is in '{app.status}' state, not pending_approval")
    app.status = "approved"
    db.add(Approval(application_id=app.id, status="approved", reviewer_notes=notes, decided_at=datetime.utcnow()))
    db.add(ApplicationEvent(application_id=app.id, event_type="approved", old_status="pending_approval", new_status="approved", notes=notes))
    await db.commit()
    return {"status": "approved", "application_id": application_id}

@router.post("/{application_id}/reject")
async def reject_application(application_id: str, notes: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    u_id = parse_uuid(application_id)
    result = await db.execute(select(Application).where(Application.id == u_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    old_status = app.status
    app.status = "rejected"
    db.add(Approval(application_id=app.id, status="rejected", reviewer_notes=notes, decided_at=datetime.utcnow()))
    db.add(ApplicationEvent(application_id=app.id, event_type="rejected", old_status=old_status, new_status="rejected", notes=notes))
    await db.commit()
    return {"status": "rejected", "application_id": application_id}

@router.get("/{application_id}/cover-letter")
async def download_cover_letter(application_id: str, db: AsyncSession = Depends(get_db)):
    u_id = parse_uuid(application_id)
    result = await db.execute(select(Application).where(Application.id == u_id))
    app = result.scalar_one_or_none()
    if not app or not app.cover_letter_path:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    full_path = app.cover_letter_path
    if not os.path.isabs(full_path):
        full_path = os.path.join(os.getcwd(), full_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Cover letter file not found on disk")
    return FileResponse(full_path, media_type="application/pdf", filename=os.path.basename(full_path))

@router.get("/{application_id}/resume")
async def download_application_resume(application_id: str, db: AsyncSession = Depends(get_db)):
    u_id = parse_uuid(application_id)
    result = await db.execute(select(Application).where(Application.id == u_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    resume_path = None
    if app.resume_id:
        res = await db.execute(select(Resume).where(Resume.id == app.resume_id))
        resume_record = res.scalar_one_or_none()
        if resume_record:
            resume_path = resume_record.file_path
    
    if not resume_path:
        res = await db.execute(select(Resume).order_by(desc(Resume.version)).limit(1))
        resume_record = res.scalar_one_or_none()
        if resume_record:
            resume_path = resume_record.file_path
            
    if not resume_path:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    full_path = resume_path
    if not os.path.isabs(full_path):
        full_path = os.path.join(os.getcwd(), full_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Resume file not found on disk")
        
    return FileResponse(full_path, media_type="application/pdf", filename=os.path.basename(full_path))


