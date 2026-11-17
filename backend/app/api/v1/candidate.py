import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.candidate import CandidateProfile, Resume, CandidateFact, JobPreference
from app.config import settings
import aiofiles

router = APIRouter()

def extract_text_from_bytes(contents: bytes, ext: str) -> str:
    try:
        if ext == "pdf":
            import PyPDF2
            import io
            reader = PyPDF2.PdfReader(io.BytesIO(contents))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext == "docx":
            import docx
            import io
            doc = docx.Document(io.BytesIO(contents))
            return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        return f"[Text extraction failed: {e}]"
    return ""

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
    
    contents = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.max_upload_size_mb}MB limit.")
    
    ext = "pdf" if "pdf" in (file.content_type or "") else "docx"
    file_id = uuid.uuid4()
    filename = f"{file_id}.{ext}"
    filepath = os.path.join(settings.upload_dir, filename)
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(contents)
    
    extracted_text = extract_text_from_bytes(contents, ext)
    
    result = await db.execute(select(CandidateProfile).limit(1))
    candidate = result.scalar_one_or_none()
    if not candidate:
        candidate = CandidateProfile(full_name="Candidate", email="candidate@example.com")
        db.add(candidate)
        await db.flush()
    
    res_result = await db.execute(select(Resume).where(Resume.candidate_id == candidate.id))
    existing = res_result.scalars().all()
    version = len(existing) + 1
    
    resume = Resume(
        candidate_id=candidate.id,
        version=version,
        file_path=filepath,
        file_name=file.filename or filename,
        file_type=ext,
        extracted_text=extracted_text,
        is_original=(version == 1),
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    
    return {
        "resume_id": str(resume.id),
        "candidate_id": str(candidate.id),
        "version": version,
        "file_name": resume.file_name,
        "extracted_text_preview": extracted_text[:500] if extracted_text else None,
    }

@router.get("/profile")
async def get_profile(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CandidateProfile).limit(1))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="No candidate profile found. Please upload your resume first.")
    facts_result = await db.execute(select(CandidateFact).where(CandidateFact.candidate_id == candidate.id))
    facts = facts_result.scalars().all()
    return {
        "id": str(candidate.id),
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "linkedin_url": candidate.linkedin_url,
        "github_url": candidate.github_url,
        "experience_years": candidate.experience_years,
        "facts": [{"id": str(f.id), "type": f.fact_type, "data": f.fact_data, "verified": f.is_verified} for f in facts],
    }

@router.put("/profile")
async def update_profile(data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CandidateProfile).limit(1))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="No candidate profile found.")
    for key, value in data.items():
        if hasattr(candidate, key) and key not in ("id", "created_at"):
            setattr(candidate, key, value)
    await db.commit()
    return {"status": "updated"}

@router.get("/preferences")
async def get_preferences(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CandidateProfile).limit(1))
    candidate = result.scalar_one_or_none()
    if not candidate:
        return _default_preferences()
    pref_result = await db.execute(select(JobPreference).where(JobPreference.candidate_id == candidate.id))
    pref = pref_result.scalar_one_or_none()
    if not pref:
        return _default_preferences()
    return {
        "target_roles": pref.target_roles,
        "preferred_locations": pref.preferred_locations,
        "work_types": pref.work_types,
        "min_salary": pref.min_salary,
        "max_salary": pref.max_salary,
        "experience_level": pref.experience_level,
        "experience_years": pref.experience_years,
        "discovery_morning": pref.discovery_morning,
        "discovery_evening": pref.discovery_evening,
        "discovery_timezone": pref.discovery_timezone,
        "llm_provider": pref.llm_provider,
    }

def _default_preferences():
    return {
        "target_roles": ["Software Development / SDE", "AI / ML Engineer", "AI & SaaS Support Engineer", "Graduate Engineer Trainee", "Python Developer", "Research Intern"],
        "preferred_locations": ["Bangalore", "Chennai", "Hyderabad", "Pune", "Remote", "Mumbai", "Kolkata", "Delhi NCR"],
        "work_types": ["remote", "hybrid", "onsite"],
        "experience_level": "fresher",
        "experience_years": 0.0,
        "discovery_morning": "09:00",
        "discovery_evening": "21:00",
        "discovery_timezone": "Asia/Kolkata",
        "llm_provider": "gemini",
    }

@router.put("/preferences")
async def update_preferences(preferences: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CandidateProfile).limit(1))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="No candidate profile found.")
    pref_result = await db.execute(select(JobPreference).where(JobPreference.candidate_id == candidate.id))
    pref = pref_result.scalar_one_or_none()
    if not pref:
        pref = JobPreference(candidate_id=candidate.id)
        db.add(pref)
    for key, value in preferences.items():
        if hasattr(pref, key) and key not in ("id", "candidate_id"):
            setattr(pref, key, value)
    await db.commit()
    return {"status": "updated"}

@router.get("/resumes")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CandidateProfile).limit(1))
    candidate = result.scalar_one_or_none()
    if not candidate:
        return []
    res_result = await db.execute(select(Resume).where(Resume.candidate_id == candidate.id).order_by(Resume.version))
    resumes = res_result.scalars().all()
    return [
        {
            "id": str(r.id),
            "version": r.version,
            "file_name": r.file_name,
            "file_type": r.file_type,
            "is_original": r.is_original,
            "target_role": r.target_role,
            "is_verified": r.is_verified,
            "created_at": r.created_at.isoformat(),
        }
        for r in resumes
    ]
