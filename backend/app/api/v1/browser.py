import os
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.browser import BrowserSession

router = APIRouter()

SCREENSHOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads/screenshots"))

@router.get("/sessions")
async def list_browser_sessions(limit: int = Query(25, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """List recent Playwright browser automation sessions and field mappings."""
    q = select(BrowserSession).order_by(desc(BrowserSession.created_at)).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(s.id),
            "workflow_run_id": str(s.workflow_run_id) if s.workflow_run_id else None,
            "application_id": str(s.application_id) if s.application_id else None,
            "portal_url": s.portal_url,
            "portal_type": s.portal_type,
            "ats_type": s.portal_type,
            "status": s.status,
            "success": s.submission_success if s.submission_success is not None else (s.status == "submitted"),
            "anti_bot_detected": s.anti_bot_detected,
            "anti_bot_details": s.anti_bot_details,
            "detected_fields": s.detected_fields or [],
            "staged_answers": s.staged_answers or {},
            "field_mappings": s.staged_answers or {},
            "resume_uploaded": s.resume_uploaded,
            "cover_letter_uploaded": s.cover_letter_uploaded,
            "pre_screenshot_url": f"http://localhost:8000/api/v1/browser/screenshots/{os.path.basename(s.pre_submit_screenshot_path)}" if s.pre_submit_screenshot_path else None,
            "post_screenshot_url": f"http://localhost:8000/api/v1/browser/screenshots/{os.path.basename(s.post_submit_screenshot_path)}" if s.post_submit_screenshot_path else None,
            "created_at": s.created_at.isoformat(),
        }
        for s in rows
    ]

@router.get("/screenshots/{filename}")
async def get_browser_screenshot(filename: str):
    """Serve captured Playwright screenshot image."""
    safe_filename = os.path.basename(filename)
    full_path = os.path.join(SCREENSHOT_DIR, safe_filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(full_path, media_type="image/png")
