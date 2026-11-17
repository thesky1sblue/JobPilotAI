from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.applications import Application, Approval, ApplicationEvent
from typing import Optional
from datetime import datetime

router = APIRouter()

@router.get("/")
async def list_applications(db: AsyncSession = Depends(get_db), status: Optional[str] = None):
    q = select(Application)
    if status:
        q = q.where(Application.status == status)
    result = await db.execute(q)
    apps = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "job_id": str(a.job_id),
            "status": a.status,
            "is_ready": a.is_ready,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in apps
    ]

@router.get("/{application_id}")
async def get_application(application_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Application).where(Application.id == application_id))
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
    result = await db.execute(select(Application).where(Application.id == application_id))
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
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    old_status = app.status
    app.status = "rejected"
    db.add(Approval(application_id=app.id, status="rejected", reviewer_notes=notes, decided_at=datetime.utcnow()))
    db.add(ApplicationEvent(application_id=app.id, event_type="rejected", old_status=old_status, new_status="rejected", notes=notes))
    await db.commit()
    return {"status": "rejected", "application_id": application_id}
