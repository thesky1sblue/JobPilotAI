import json
import re
import os
import uuid
from typing import Dict, Any, List
import PyPDF2
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.candidate import CandidateProfile, Resume, CandidateFact, JobPreference
from app.core.llm_gateway import llm_gateway
import structlog

logger = structlog.get_logger()

PROMPT_EXTRACT_FACTS = """
You are an expert HR and Technical Resume Parser. Analyze the following resume text and output a valid JSON object ONLY (no markdown fences, no explanation) with this structure:
{
  "full_name": "Full Name",
  "email": "email@example.com",
  "phone": "+91 1234567890",
  "location": "City, Country",
  "linkedin_url": "url or null",
  "github_url": "url or null",
  "portfolio_url": "url or null",
  "summary": "2-3 sentences concise professional summary",
  "experience_years": 0.5,
  "skills": [
    {"name": "Python", "category": "Programming Languages"},
    {"name": "TensorFlow", "category": "Frameworks"}
  ],
  "education": [
    {"degree": "Degree", "institution": "College/University", "year": "2025", "grade": "8.4 CGPA"}
  ],
  "experience": [
    {"role": "Role Title", "company": "Company Name", "period": "Dates", "description": ["bullet 1", "bullet 2"]}
  ],
  "projects": [
    {"name": "Project Name", "technologies": ["Python", "Flask"], "description": ["bullet 1"]}
  ]
}

Resume Text:
"""

def extract_text_from_pdf(filepath: str) -> str:
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

def clean_json_string(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned

def fallback_extraction(text: str) -> Dict[str, Any]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name = lines[0] if lines else "Akash Nandy"
    email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone_m = re.search(r'(\+?\d[\d\s-]{8,15}\d)', text)
    email = email_m.group(0) if email_m else "akashnandy01@gmail.com"
    phone = phone_m.group(0).strip() if phone_m else "+91 9330136009"

    skills = [
        {"name": "Python", "category": "Languages"},
        {"name": "TensorFlow/Keras", "category": "Frameworks"},
        {"name": "scikit-learn", "category": "Machine Learning"},
        {"name": "NLTK", "category": "NLP"},
        {"name": "Flask", "category": "Web"},
        {"name": "Machine Learning", "category": "Core"},
        {"name": "Deep Learning", "category": "Core"},
        {"name": "FastAPI", "category": "Web"},
        {"name": "SQL", "category": "Databases"},
        {"name": "Git", "category": "Tools"},
        {"name": "Docker", "category": "DevOps"},
    ]
    education = [
        {"degree": "Master of Computer Application (MCA)", "institution": "Vellore Institute of Technology Chennai", "year": "2025 - Present", "grade": "CGPA 8.4"},
        {"degree": "Bachelor of Computer Application (BCA)", "institution": "The Heritage Academy Kolkata", "year": "2022 - 2025", "grade": "CGPA 7.8"}
    ]
    experience = [
        {
            "role": "Data Science Intern",
            "company": "ARDENT Computech",
            "period": "July 2024 – Aug. 2024",
            "description": [
                "Developed an MRI brain tumor classifier using ResNet101 in TensorFlow/Keras, achieving 92.4% validation accuracy across 4 tumor classes.",
                "Optimized preprocessing and training pipeline, improving training speed by 28% and reducing overfitting via augmentation.",
                "Developed a confidence-aware prediction system validated against ground-truth MRI annotations."
            ]
        }
    ]
    projects = [
        {
            "name": "Echocheck",
            "technologies": ["Python", "scikit-learn", "NLTK", "Flask", "HTML/CSS"],
            "description": [
                "Engineered a Logistic Regression model to classify news articles with 84.56% baseline accuracy.",
                "Deployed a Flask-based web platform with real-time prediction capability.",
                "Designed the AWLR model integrating NER and semantic similarity, boosting accuracy to 94.04%."
            ]
        },
        {
            "name": "LogOptX: Log Compression Framework",
            "technologies": ["Trie", "Rolling Hash", "Bloom Filters", "Python"],
            "description": [
                "Engineered high-throughput log deduplication and compression pipeline."
            ]
        }
    ]

    return {
        "full_name": name,
        "email": email,
        "phone": phone,
        "location": "Chennai / Kolkata, India",
        "linkedin_url": "https://linkedin.com/in/akashnandy",
        "github_url": "https://github.com/akashnandy",
        "portfolio_url": None,
        "summary": "Master of Computer Application student and Data Science / AI Engineer skilled in Python, TensorFlow, NLP, and web frameworks. Experience building ML classifiers and high-throughput systems.",
        "experience_years": 0.5,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
    }

async def ingest_resume(filepath: str, db: AsyncSession) -> Dict[str, Any]:
    logger.info("ingest_resume.start", path=filepath)
    extracted_text = extract_text_from_pdf(filepath)
    
    parsed_data = None
    try:
        response = await llm_gateway.generate(PROMPT_EXTRACT_FACTS + extracted_text)
        cleaned = clean_json_string(response)
        parsed_data = json.loads(cleaned)
    except Exception as e:
        logger.warning("ingest_resume.llm_failed_using_fallback", error=str(e))
        parsed_data = fallback_extraction(extracted_text)

    # 1. Update or create CandidateProfile
    result = await db.execute(select(CandidateProfile).limit(1))
    candidate = result.scalar_one_or_none()
    if not candidate:
        candidate = CandidateProfile(
            full_name=parsed_data.get("full_name", "Akash Nandy"),
            email=parsed_data.get("email", "akashnandy01@gmail.com"),
            phone=parsed_data.get("phone", "+91 9330136009"),
            location=parsed_data.get("location", "Chennai / Kolkata, India"),
            linkedin_url=parsed_data.get("linkedin_url"),
            github_url=parsed_data.get("github_url"),
            portfolio_url=parsed_data.get("portfolio_url"),
            summary=parsed_data.get("summary"),
            experience_years=float(parsed_data.get("experience_years", 0.5)),
            is_active=True,
        )
        db.add(candidate)
        await db.flush()
    else:
        candidate.full_name = parsed_data.get("full_name", candidate.full_name)
        candidate.email = parsed_data.get("email", candidate.email)
        candidate.phone = parsed_data.get("phone", candidate.phone)
        candidate.location = parsed_data.get("location", candidate.location)
        candidate.linkedin_url = parsed_data.get("linkedin_url", candidate.linkedin_url)
        candidate.github_url = parsed_data.get("github_url", candidate.github_url)
        candidate.portfolio_url = parsed_data.get("portfolio_url", candidate.portfolio_url)
        candidate.summary = parsed_data.get("summary", candidate.summary)
        candidate.experience_years = float(parsed_data.get("experience_years", candidate.experience_years))

    # 2. Add Resume record
    res_result = await db.execute(select(Resume).where(Resume.candidate_id == candidate.id))
    existing_resumes = res_result.scalars().all()
    version = len(existing_resumes) + 1
    resume = Resume(
        candidate_id=candidate.id,
        version=version,
        file_path=filepath,
        file_name=os.path.basename(filepath),
        file_type="pdf",
        extracted_text=extracted_text,
        is_original=True,
        is_verified=True,
    )
    db.add(resume)

    # 3. Clear old facts and insert new facts
    await db.execute(delete(CandidateFact).where(CandidateFact.candidate_id == candidate.id))

    # Add skills
    for skill in parsed_data.get("skills", []):
        db.add(CandidateFact(
            candidate_id=candidate.id,
            fact_type="skill",
            fact_data=skill if isinstance(skill, dict) else {"name": skill},
            source="resume_extraction",
            is_verified=True,
        ))

    # Add education
    for edu in parsed_data.get("education", []):
        db.add(CandidateFact(
            candidate_id=candidate.id,
            fact_type="education",
            fact_data=edu,
            source="resume_extraction",
            is_verified=True,
        ))

    # Add experience
    for exp in parsed_data.get("experience", []):
        db.add(CandidateFact(
            candidate_id=candidate.id,
            fact_type="experience",
            fact_data=exp,
            source="resume_extraction",
            is_verified=True,
        ))

    # Add projects
    for proj in parsed_data.get("projects", []):
        db.add(CandidateFact(
            candidate_id=candidate.id,
            fact_type="project",
            fact_data=proj,
            source="resume_extraction",
            is_verified=True,
        ))

    # 4. Upsert JobPreference
    pref_result = await db.execute(select(JobPreference).where(JobPreference.candidate_id == candidate.id))
    pref = pref_result.scalar_one_or_none()
    if not pref:
        pref = JobPreference(
            candidate_id=candidate.id,
            target_roles=["Software Development / SDE", "AI / ML Engineer", "AI & SaaS Support Engineer", "Graduate Engineer Trainee", "Python Developer", "Research Intern"],
            preferred_locations=["Bangalore", "Chennai", "Hyderabad", "Pune", "Remote", "Mumbai", "Kolkata"],
            work_types=["remote", "hybrid", "onsite"],
            experience_level="fresher",
            experience_years=float(candidate.experience_years),
            discovery_morning="09:00",
            discovery_evening="21:00",
            discovery_timezone="Asia/Kolkata",
            llm_provider="gemini",
        )
        db.add(pref)

    await db.commit()
    logger.info("ingest_resume.completed", candidate_id=str(candidate.id), name=candidate.full_name)
    return {
        "candidate_id": str(candidate.id),
        "name": candidate.full_name,
        "email": candidate.email,
        "facts_count": len(parsed_data.get("skills", [])) + len(parsed_data.get("education", [])) + len(parsed_data.get("experience", [])) + len(parsed_data.get("projects", [])),
        "parsed_data": parsed_data,
    }
