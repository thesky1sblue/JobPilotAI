import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.gmail import GmailMessage
from app.services.gmail_service import gmail_service

router = APIRouter()

@router.get("/messages")
async def list_recruitment_emails(
    classification: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve scanned recruitment emails with AI classifications and action items."""
    q = select(GmailMessage).order_by(desc(GmailMessage.received_at)).limit(limit)
    if classification:
        q = q.where(GmailMessage.classification == classification)

    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(m.id),
            "message_id": m.message_id,
            "thread_id": m.thread_id,
            "sender": m.sender,
            "sender_name": m.sender_name,
            "recipient": m.recipient,
            "subject": m.subject,
            "snippet": m.snippet,
            "body_text": m.body_text,
            "classification": m.classification,
            "confidence_score": m.confidence_score,
            "action_required": m.action_required,
            "action_summary": m.action_summary,
            "deadline": m.deadline.isoformat() if m.deadline else None,
            "linked_company_id": str(m.linked_company_id) if m.linked_company_id else None,
            "linked_application_id": str(m.linked_application_id) if m.linked_application_id else None,
            "received_at": m.received_at.isoformat(),
        }
        for m in rows
    ]

@router.post("/sync")
async def sync_recruitment_emails(db: AsyncSession = Depends(get_db)):
    """Trigger synchronous scan of candidate mailbox for recruitment messages."""
    results = await gmail_service.sync_emails(db)
    return {
        "status": "success",
        "synced_count": len(results),
        "messages": results,
    }
