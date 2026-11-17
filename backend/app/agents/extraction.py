import re
from typing import Any, Dict, List, Optional
from app.agents.base import BaseAgent

SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "java", "golang", "rust", "c++", "c#",
    "react", "nextjs", "angular", "vue", "nodejs", "fastapi", "django", "flask",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
    "machine learning", "deep learning", "pytorch", "tensorflow", "sklearn",
    "langchain", "langgraph", "openai", "llm", "nlp",
    "git", "linux", "rest api", "graphql", "kafka", "spark",
]

def extract_skills_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        if skill in text_lower:
            found.append(skill)
    return found

def detect_location_type(location: str) -> str:
    loc = (location or "").lower()
    if "remote" in loc:
        return "remote"
    if "hybrid" in loc:
        return "hybrid"
    return "onsite"

def extract_experience(text: str) -> Optional[int]:
    patterns = [
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\s*-\s*\d+\s*years?',
        r'experience\s*of\s*(\d+)\+?\s*years?',
        r'fresher|0-1 year|entry.level|graduate',
    ]
    text_lower = text.lower()
    if re.search(r'fresher|0-1 year|entry.level|graduate', text_lower):
        return 0
    for p in patterns[:3]:
        m = re.search(p, text_lower)
        if m:
            return int(m.group(1))
    return None

class ExtractionAgent(BaseAgent):
    name = "extraction_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        raw_job = input_data["raw_job"]
        description = raw_job.get("description", "") or ""
        title = raw_job.get("title", "")
        location = raw_job.get("location", "")

        required_skills = extract_skills_from_text(description + " " + title)
        exp_min = extract_experience(description)
        location_type = detect_location_type(location)

        return {
            "title": title,
            "description": description,
            "location": location,
            "location_type": location_type,
            "source": raw_job.get("source", ""),
            "source_id": raw_job.get("source_id", ""),
            "application_url": raw_job.get("application_url", ""),
            "department": raw_job.get("department", ""),
            "posted_at": raw_job.get("posted_at"),
            "required_skills": required_skills,
            "experience_min": exp_min,
            "raw_payload": raw_job,
        }
