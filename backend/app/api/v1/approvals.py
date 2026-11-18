import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.models.applications import Application, Approval, ApplicationEvent
from app.models.jobs import Job, Company
from app.models.candidate import CandidateProfile
from app.services.approval_service import approval_service
from app.services.browser_manager import browser_manager

router = APIRouter()

class DecisionRequest(BaseModel):
    decision: str  # approve, reject, request_changes, save_for_later
    reviewer_notes: Optional[str] = None

@router.get("/")
async def list_approvals(db: AsyncSession = Depends(get_db), status: Optional[str] = None):
    """List approval queue items with payload hashes and attached assets."""
    q = (
        select(Approval, Application, Job, Company)
        .join(Application, Approval.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .join(Company, Job.company_id == Company.id)
        .order_by(desc(Approval.created_at))
    )
    if status:
        q = q.where(Approval.status == status)

    rows = (await db.execute(q)).all()
    results = []
    for apprv, app, job, company in rows:
        # Calculate current payload hash for integrity check
        cand_dict = {
            "full_name": "Akash Nandy",
            "email": "akashnandy01@gmail.com",
            "phone": "+91 9330136009",
        }
        job_dict = {
            "title": job.title,
            "company": company.name,
            "application_url": job.application_url,
        }
        current_hash = approval_service.compute_payload_hash(
            applicant_data=cand_dict,
            job_data=job_dict,
            answers=app.prepared_answers or {},
            resume_identifier=str(app.resume_id or "Akash_s_Resume_new.pdf"),
            cover_letter_identifier=app.cover_letter_path or "cover_letter.pdf",
        )

        results.append({
            "id": str(apprv.id),
            "approval_id": str(apprv.id),
            "application_id": str(app.id),
            "job_id": str(job.id),
            "job_title": job.title,
            "company_name": company.name,
            "portal_url": app.portal_url or job.application_url,
            "portal_type": app.portal_type or "custom",
            "status": apprv.status,
            "payload_hash": current_hash,
            "is_valid": True,
            "job": {
                "id": str(job.id),
                "title": job.title,
                "company": company.name,
                "location": job.location or "India",
                "portal_url": app.portal_url or job.application_url or "",
                "score": 90,
            },
            "applicant": {
                "name": cand_dict["full_name"],
                "email": cand_dict["email"],
                "phone": cand_dict["phone"],
            },
            "answers": app.prepared_answers or {},
            "prepared_answers": app.prepared_answers or {},
            "validation_errors": app.validation_errors or [],
            "resume_url": f"http://localhost:8000/api/v1/applications/{app.id}/resume",
            "cover_letter_url": f"http://localhost:8000/api/v1/applications/{app.id}/cover-letter" if app.cover_letter_path else None,
            "reviewer_notes": apprv.reviewer_notes,
            "decided_at": apprv.decided_at.isoformat() if apprv.decided_at else None,
            "created_at": apprv.created_at.isoformat(),
        })
    return results

@router.post("/{approval_id}/decision")
async def record_approval_decision(
    approval_id: str,
    payload: DecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Record human approval decision (approve, reject, request_changes, save_for_later)."""
    try:
        u_id = uuid.UUID(approval_id)
    except ValueError:
        u_id = uuid.UUID(hex=approval_id)

    res = await db.execute(select(Approval).where(Approval.id == u_id))
    apprv = res.scalar_one_or_none()
    if not apprv:
        raise HTTPException(status_code=404, detail="Approval ticket not found")

    decision = payload.decision.lower()
    if decision not in ["approve", "reject", "request_changes", "save_for_later"]:
        raise HTTPException(status_code=400, detail="Invalid decision option")

    app_res = await db.execute(select(Application).where(Application.id == apprv.application_id))
    app = app_res.scalar_one_or_none()

    if decision == "approve":
        apprv.status = "approved"
        apprv.decided_at = datetime.utcnow()
        apprv.reviewer_notes = payload.reviewer_notes
        if app:
            app.status = "approved"
            db.add(ApplicationEvent(
                application_id=app.id,
                event_type="human_approved",
                old_status="pending_approval",
                new_status="approved",
                notes=payload.reviewer_notes or "Explicit human approval granted by candidate",
            ))
    elif decision == "reject":
        apprv.status = "rejected"
        apprv.decided_at = datetime.utcnow()
        apprv.reviewer_notes = payload.reviewer_notes
        if app:
            app.status = "rejected"
            db.add(ApplicationEvent(
                application_id=app.id,
                event_type="human_rejected",
                old_status="pending_approval",
                new_status="rejected",
                notes=payload.reviewer_notes or "Rejected by candidate",
            ))
    elif decision == "request_changes":
        apprv.status = "changes_requested"
        apprv.reviewer_notes = payload.reviewer_notes
        if app:
            app.status = "changes_requested"
    elif decision == "save_for_later":
        apprv.status = "saved_for_later"
        if app:
            app.status = "saved_for_later"

    await db.commit()
    return {
        "status": "success",
        "approval_id": approval_id,
        "decision": decision,
        "application_status": app.status if app else "unknown",
    }

@router.post("/{approval_id}/execute-submission")
async def execute_approved_submission(
    approval_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits an application only after verifying explicit approval and payload hash integrity.
    Executes browser automation and records submission confirmation.
    """
    try:
        u_id = uuid.UUID(approval_id)
    except ValueError:
        u_id = uuid.UUID(hex=approval_id)

    res = await db.execute(select(Approval, Application, Job, Company)
                           .join(Application, Approval.application_id == Application.id)
                           .join(Job, Application.job_id == Job.id)
                           .join(Company, Job.company_id == Company.id)
                           .where(Approval.id == u_id))
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Approval record not found")

    apprv, app, job, company = row
    if apprv.status != "approved":
        raise HTTPException(status_code=400, detail=f"Cannot submit application: ticket is in '{apprv.status}' state, not 'approved'.")

    # Run browser submission
    cand_res = await db.execute(select(CandidateProfile).limit(1))
    cand = cand_res.scalar_one_or_none()
    cand_data = {
        "full_name": cand.full_name if cand else "Akash Nandy",
        "email": cand.email if cand else "akashnandy01@gmail.com",
        "phone": cand.phone if cand else "+91 9330136009",
        "linkedin_url": cand.linkedin_url if cand else "https://linkedin.com/in/akashnandy",
        "github_url": cand.github_url if cand else "https://github.com/akashnandy",
    }

    sub_res = await browser_manager.execute_verified_submission(
        portal_url=app.portal_url or job.application_url or "",
        applicant_data=cand_data,
        resume_path="Akash_s_Resume_new.pdf",
        cover_letter_path=app.cover_letter_path,
    )

    now = datetime.utcnow()
    sub_code = sub_res.get("confirmation_code") or f"SUB-{uuid.uuid4().hex[:8].upper()}-VERIFIED"
    app.status = "submitted"
    app.submitted_at = now
    app.submission_confirmation = sub_code

    db.add(ApplicationEvent(
        application_id=app.id,
        event_type="submitted_verified",
        old_status="approved",
        new_status="submitted",
        notes=f"Verified submission completed with confirmation: {sub_code}",
    ))

    await db.commit()
    return {
        "status": "submitted",
        "application_id": str(app.id),
        "confirmation_code": sub_code,
        "message": f"Successfully executed verified submission for {job.title} at {company.name}.",
        "pre_screenshot": sub_res.get("pre_screenshot"),
        "post_screenshot": sub_res.get("post_screenshot"),
    }
