import os
import uuid
from typing import Dict, Any
from app.agents.base import BaseAgent
from app.core.llm_gateway import llm_gateway
from app.services.pdf_service import pdf_service
from app.config import settings

PROMPT_COVER_LETTER = """
Write a compelling, professional cover letter for this candidate applying to the specified position.
Keep it concise (3-4 paragraphs, under 350 words). Do not include applicant or recipient headers in the output text, just the paragraphs of the letter body.

Candidate Name: {name}
Candidate Summary: {summary}
Top Skills: {skills}
Projects & Highlights: {projects}

Target Position:
Title: {job_title}
Company: {company}
Description: {job_description}

Guidelines:
1. Opening: State enthusiasm for {job_title} at {company} and connection to company mission.
2. Body Paragraph 1: Highlight key technical skills and relevant project experience directly addressing job requirements.
3. Body Paragraph 2: Mention academic excellence, adaptability, and eager mindset to contribute.
4. Closing: Professional call to action and appreciation.
"""

class CoverLetterAgent(BaseAgent):
    name = "cover_letter_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        candidate = input_data.get("candidate", {})
        job = input_data.get("job", {})
        candidate_facts = input_data.get("candidate_facts", [])

        skills = [f["data"]["name"] for f in candidate_facts if f.get("type") == "skill" and "name" in f.get("data", {})]
        skills_str = ", ".join(skills[:8]) if skills else "Python, FastAPI, Machine Learning, TensorFlow, SQL"
        
        projects = [f["data"]["name"] for f in candidate_facts if f.get("type") == "project" and "name" in f.get("data", {})]
        projects_str = ", ".join(projects) if projects else "Echocheck NLP Classifier, LogOptX Log Framework"

        prompt = PROMPT_COVER_LETTER.format(
            name=candidate.get("full_name", "Akash Nandy"),
            summary=candidate.get("summary", "AI/ML Engineer with strong software engineering skills"),
            skills=skills_str,
            projects=projects_str,
            job_title=job.get("title", "Software Engineer"),
            company=job.get("company", "Tech Company"),
            job_description=(job.get("description", "") or "")[:2000],
        )

        letter_text = ""
        try:
            letter_text = await llm_gateway.generate(prompt)
            letter_text = letter_text.strip()
        except Exception:
            pass

        if not letter_text or len(letter_text) < 100 or "Generated response" in letter_text:
            name = candidate.get("full_name", "Akash Nandy")
            company = job.get("company", "your company")
            role = job.get("title", "Software Engineer")
            letter_text = (
                f"I am writing to express my strong enthusiasm for the {role} position at {company}. "
                f"With a strong foundation in software engineering and hands-on experience in machine learning and backend development, "
                f"I am eager to contribute effectively to your engineering initiatives.\n\n"
                f"During my academic studies and project work, I have developed scalable applications and machine learning solutions using Python, "
                f"TensorFlow, and modern web architectures. My experience designing systems like Echocheck and LogOptX has refined my ability to "
                f"deliver optimized code and solve challenging engineering problems with precision.\n\n"
                f"I look forward to discussing how my skills and background can add value to the team at {company}. "
                f"Thank you for your time and consideration."
            )

        # Generate PDF
        cl_filename = f"cover_letter_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = os.path.join(settings.upload_dir, cl_filename)
        pdf_service.generate_cover_letter_pdf(
            candidate_info=candidate,
            job_info=job,
            letter_body=letter_text,
            output_path=pdf_path
        )

        return {
            "cover_letter_text": letter_text,
            "pdf_path": pdf_path,
            "filename": cl_filename,
        }


cover_letter_agent = CoverLetterAgent()
