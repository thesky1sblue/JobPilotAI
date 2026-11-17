from typing import Any, Dict, List
from app.agents.base import BaseAgent

WEIGHTS = {"skill": 0.30, "role": 0.25, "experience": 0.15, "location": 0.10, "salary": 0.10, "education": 0.10}

def classify(score: float) -> str:
    if score >= 85: return "strong"
    if score >= 70: return "good"
    if score >= 55: return "review"
    return "low"

class MatchingAgent(BaseAgent):
    name = "matching_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        job = input_data["job"]
        candidate_facts = input_data.get("candidate_facts", [])
        preferences = input_data.get("preferences", {})

        candidate_skills = set()
        for fact in candidate_facts:
            if fact.get("type") == "skill":
                skill = fact.get("data", {}).get("name", "").lower().strip()
                if skill:
                    candidate_skills.add(skill)

        required_skills = [s.lower() for s in (job.get("required_skills") or [])]
        matched = [s for s in required_skills if s in candidate_skills]
        missing = [s for s in required_skills if s not in candidate_skills]

        skill_score = (len(matched) / len(required_skills)) * 100 if required_skills else 70.0

        job_title = job.get("title", "").lower()
        role_keywords = ["software", "developer", "engineer", "ai", "ml", "python", "intern", "research", "sde", "get", "data", "backend", "frontend", "fullstack", "cloud"]
        role_score = 85.0 if any(k in job_title for k in role_keywords) else 60.0

        exp_min = job.get("experience_min")
        candidate_exp = preferences.get("experience_years", 0)
        is_eligible = True
        eligibility_notes = ""
        if exp_min is not None and exp_min > 1 and candidate_exp < exp_min:
            is_eligible = False
            experience_score = 20.0
            eligibility_notes = f"Requires {exp_min}+ years; candidate has {candidate_exp}"
        elif exp_min is None or exp_min <= 1:
            experience_score = 90.0
        else:
            experience_score = 75.0

        preferred_locations = [l.lower() for l in (preferences.get("preferred_locations") or [])]
        job_location = (job.get("location") or "").lower()
        if not job_location:
            location_score = 70.0
        elif "remote" in job_location:
            location_score = 100.0
        elif any(l in job_location for l in preferred_locations):
            location_score = 90.0
        else:
            location_score = 40.0

        salary_score = 80.0
        education_score = 80.0

        overall = (
            skill_score * WEIGHTS["skill"] + role_score * WEIGHTS["role"] +
            experience_score * WEIGHTS["experience"] + location_score * WEIGHTS["location"] +
            salary_score * WEIGHTS["salary"] + education_score * WEIGHTS["education"]
        )

        lines = [f"Overall match: {overall:.1f}%"]
        if matched: lines.append(f"Skills matched: {', '.join(matched[:5])}")
        if missing: lines.append(f"Skills to develop: {', '.join(missing[:5])}")

        return {
            "overall_score": round(overall, 1),
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
            "classification": classify(overall),
            "explanation": ". ".join(lines),
        }
