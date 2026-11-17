import os
import json
import uuid
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.core.llm_gateway import llm_gateway
from app.services.pdf_service import pdf_service
from app.config import settings

PROMPT_TAILOR_RESUME = """
You are an expert Resume Strategist and Technical Recruiter. Tailor the candidate's resume for the specific target job without inventing false facts.

Candidate Profile and Facts:
{candidate_facts}

Target Job:
Title: {job_title}
Company: {company}
Description: {job_description}
Required Skills: {required_skills}

Output a strictly valid JSON object with:
{{
  "full_name": "{candidate_name}",
  "email": "{candidate_email}",
  "phone": "{candidate_phone}",
  "location": "{candidate_location}",
  "linkedin_url": "{candidate_linkedin}",
  "github_url": "{candidate_github}",
  "summary": "Targeted 3-sentence summary emphasizing relevance to {job_title} at {company}",
  "skills": ["Skill 1", "Skill 2"],
  "experience": [
    {{
      "role": "Role",
      "company": "Company",
      "period": "Dates",
      "description": ["Action-verb bullet highlighting relevant skills and outcomes", "Second bullet"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "technologies": ["Tech 1", "Tech 2"],
      "description": ["Action bullet tailored toward the target tech stack"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree",
      "institution": "Institution",
      "year": "Dates"
    }}
  ]
}}
"""

class ResumeIntelligenceAgent(BaseAgent):
    name = "resume_intelligence_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        candidate = input_data.get("candidate", {})
        candidate_facts = input_data.get("candidate_facts", [])
        job = input_data.get("job", {})

        prompt = PROMPT_TAILOR_RESUME.format(
            candidate_facts=json.dumps(candidate_facts, indent=2),
            candidate_name=candidate.get("full_name", "Akash Nandy"),
            candidate_email=candidate.get("email", "akashnandy01@gmail.com"),
            candidate_phone=candidate.get("phone", "+91 9330136009"),
            candidate_location=candidate.get("location", "Chennai / Kolkata, India"),
            candidate_linkedin=candidate.get("linkedin_url", "https://linkedin.com/in/akashnandy"),
            candidate_github=candidate.get("github_url", "https://github.com/akashnandy"),
            job_title=job.get("title", "Software Engineer"),
            company=job.get("company", "Tech Company"),
            job_description=(job.get("description", "") or "")[:2000],
            required_skills=", ".join(job.get("required_skills", []) or []),
        )

        tailored_data = None
        try:
            raw_response = await llm_gateway.generate(prompt)
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"): lines = lines[1:]
                if lines and lines[-1].startswith("```"): lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            tailored_data = json.loads(cleaned)
        except Exception:
            # Fallback to structuring from facts
            skills = [f["data"]["name"] for f in candidate_facts if f.get("type") == "skill" and "name" in f.get("data", {})]
            if not skills:
                skills = ["Python", "FastAPI", "TensorFlow", "scikit-learn", "Docker", "SQL", "Git"]
            exp = [f["data"] for f in candidate_facts if f.get("type") == "experience"]
            if not exp:
                exp = [{"role": "Data Science Intern", "company": "ARDENT Computech", "period": "July 2024 – Aug. 2024", "description": ["Developed MRI classifier with ResNet101 in TensorFlow/Keras", "Optimized preprocessing pipeline improving speed by 28%"]}]
            proj = [f["data"] for f in candidate_facts if f.get("type") == "project"]
            if not proj:
                proj = [{"name": "Echocheck", "technologies": ["Python", "Flask", "scikit-learn"], "description": ["Engineered NLP classifier achieving 94.04% accuracy"]}]
            edu = [f["data"] for f in candidate_facts if f.get("type") == "education"]
            if not edu:
                edu = [{"degree": "Master of Computer Application (MCA)", "institution": "VIT Chennai", "year": "2025-Present"}]

            tailored_data = {
                "full_name": candidate.get("full_name", "Akash Nandy"),
                "email": candidate.get("email", "akashnandy01@gmail.com"),
                "phone": candidate.get("phone", "+91 9330136009"),
                "location": candidate.get("location", "Chennai / Kolkata, India"),
                "linkedin_url": candidate.get("linkedin_url"),
                "github_url": candidate.get("github_url"),
                "summary": f"Data Science & AI Engineer with expertise in Python and machine learning, tailored for {job.get('title', 'Software Engineer')} at {job.get('company', 'Company')}.",
                "skills": skills,
                "experience": exp,
                "projects": proj,
                "education": edu,
            }

        # Generate PDF
        resume_filename = f"tailored_resume_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = os.path.join(settings.upload_dir, resume_filename)
        pdf_service.generate_resume_pdf(tailored_data, pdf_path)

        return {
            "tailored_data": tailored_data,
            "pdf_path": pdf_path,
            "resume_filename": resume_filename,
        }
