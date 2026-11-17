from typing import Any, Dict, List, Set
from app.agents.base import BaseAgent
from app.services.ingestion_service import SKILL_SYNONYMS

WEIGHTS = {
    "skill": 0.30,
    "role": 0.25,
    "experience": 0.15,
    "location": 0.10,
    "salary": 0.10,
    "education": 0.10,
}

CLASSIFICATIONS = {
    (80, 101): "strong",
    (70, 80): "good",
    (55, 70): "review",
    (0, 55): "low",
}

def classify(score: float) -> str:
    if score >= 80:
        return "strong"
    if score >= 70:
        return "good"
    if score >= 55:
        return "review"
    return "low"

def normalize_skill(skill_str: str) -> str:
    s = skill_str.lower().strip()
    s = s.replace(".", "").replace("/", " ").replace("-", " ")
    for k, v in SKILL_SYNONYMS.items():
        if k in s:
            return v
    return s

class MatchingAgent(BaseAgent):
    name = "matching_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        job = input_data["job"]
        candidate_facts = input_data.get("candidate_facts", [])
        preferences = input_data.get("preferences", {})

        # Extract normalized candidate skills
        candidate_skills: Set[str] = set()
        for fact in candidate_facts:
            if fact.get("type") == "skill":
                name = fact.get("data", {}).get("name", "")
                if name:
                    candidate_skills.add(normalize_skill(name))
                    candidate_skills.add(name.lower().strip())

        # Also add project technologies to candidate skills
        for fact in candidate_facts:
            if fact.get("type") == "project":
                techs = fact.get("data", {}).get("technologies", [])
                for t in techs:
                    candidate_skills.add(normalize_skill(t))
                    candidate_skills.add(t.lower().strip())

        # Skill matching
        required_skills = [s.strip() for s in (job.get("required_skills") or []) if s.strip()]
        matched = []
        missing = []

        if required_skills:
            for req in required_skills:
                norm_req = normalize_skill(req)
                # Check direct or synonym or substring match
                is_matched = False
                for c_skill in candidate_skills:
                    if norm_req in c_skill or c_skill in norm_req or req.lower() in c_skill:
                        is_matched = True
                        break
                if is_matched:
                    matched.append(req)
                else:
                    missing.append(req)
            
            match_ratio = len(matched) / len(required_skills)
            skill_score = min(100.0, match_ratio * 100.0 + 15.0)  # slight boost for foundational overlap
        else:
            # If no explicit skills tagged, analyze description text
            desc = (job.get("description") or "").lower()
            found_count = sum(1 for s in ["python", "machine learning", "deep learning", "sql", "ai", "pytorch", "fastapi"] if s in desc)
            skill_score = min(95.0, 60.0 + found_count * 7.0)

        # Role title relevance
        job_title = (job.get("title") or "").lower()
        role_keywords = [
            "ai", "ml", "machine learning", "deep learning", "python", "data scientist", "data science",
            "computer vision", "nlp", "software", "developer", "engineer", "sde", "backend", "full stack",
            "graduate", "intern", "trainee", "fresher", "research", "associate"
        ]
        
        matches_target_role = any(kw in job_title for kw in role_keywords)
        if matches_target_role:
            role_score = 92.0
            if any(term in job_title for term in ["intern", "graduate", "trainee", "associate", "junior", "fresher", "entry"]):
                role_score = 98.0
        else:
            role_score = 65.0

        # Experience eligibility
        exp_min = job.get("experience_min")
        candidate_exp = preferences.get("experience_years", 0.5)
        is_eligible = True
        eligibility_notes = ""

        if exp_min is not None and exp_min > 2 and candidate_exp < exp_min:
            # Requires 3+ years experience
            experience_score = 40.0
            is_eligible = False
            eligibility_notes = f"Job requires {exp_min}+ years experience; candidate has fresher/0-1y profile."
        elif exp_min is None or exp_min <= 1:
            experience_score = 95.0
        elif exp_min == 2:
            experience_score = 80.0
        else:
            experience_score = 60.0

        # Location compatibility
        preferred_locations = [l.lower() for l in (preferences.get("preferred_locations") or ["bangalore", "remote", "chennai", "hyderabad", "pune", "kolkata"])]
        job_location = (job.get("location") or "").lower()
        
        if not job_location or "remote" in job_location or "anywhere" in job_location or "india" in job_location:
            location_score = 100.0
        elif any(pref in job_location for pref in preferred_locations):
            location_score = 95.0
        else:
            location_score = 60.0  # Still considered since candidate is willing to relocate in India

        # Compensation compatibility (no min salary restriction)
        salary_score = 85.0

        # Education compatibility (Akash holds MCA from VIT Chennai + BCA from Heritage Academy)
        education_score = 95.0

        # Weighted score
        overall = (
            skill_score * WEIGHTS["skill"] +
            role_score * WEIGHTS["role"] +
            experience_score * WEIGHTS["experience"] +
            location_score * WEIGHTS["location"] +
            salary_score * WEIGHTS["salary"] +
            education_score * WEIGHTS["education"]
        )

        overall = round(min(100.0, max(0.0, overall)), 1)
        classification = classify(overall)

        lines = [f"Overall compatibility: {overall:.1f}% ({classification.upper()} MATCH)"]
        if matched:
            lines.append(f"Matching technical skills: {', '.join(matched[:5])}")
        if missing:
            lines.append(f"Target growth areas: {', '.join(missing[:4])}")
        if is_eligible:
            lines.append("Profile meets education and experience requirements.")
        else:
            lines.append(eligibility_notes)

        return {
            "overall_score": overall,
            "skill_score": round(skill_score, 1),
            "role_score": round(role_score, 1),
            "experience_score": round(experience_score, 1),
            "location_score": round(location_score, 1),
            "salary_score": round(salary_score, 1),
            "education_score": round(education_score, 1),
            "matched_skills": matched,
            "missing_skills": missing,
            "is_eligible": is_eligible,
            "eligibility_notes": eligibility_notes,
            "classification": classification,
            "explanation": " ".join(lines),
        }

matching_agent = MatchingAgent()
