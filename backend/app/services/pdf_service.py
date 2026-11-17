import os
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class PDFService:
    @staticmethod
    def generate_resume_pdf(data: Dict[str, Any], output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "NameHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1A202C"),
            alignment=TA_CENTER,
        )
        contact_style = ParagraphStyle(
            "ContactInfo",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#4A5568"),
            alignment=TA_CENTER,
        )
        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#2D3748"),
        )
        bullet_style = ParagraphStyle(
            "Bullet",
            parent=body_style,
            leftIndent=14,
            firstLineIndent=-10,
            spaceBefore=2,
            spaceAfter=2,
        )

        elements = []

        # Name and contact
        name = data.get("full_name", "Candidate")
        elements.append(Paragraph(name, title_style))
        elements.append(Spacer(1, 4))

        contacts = []
        if data.get("email"): contacts.append(data["email"])
        if data.get("phone"): contacts.append(data["phone"])
        if data.get("location"): contacts.append(data["location"])
        if data.get("linkedin_url"): contacts.append("LinkedIn")
        if data.get("github_url"): contacts.append("GitHub")
        if data.get("portfolio_url"): contacts.append("Portfolio")
        elements.append(Paragraph(" | ".join(contacts), contact_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceBefore=2, spaceAfter=8))

        # Summary
        if data.get("summary"):
            elements.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
            elements.append(Paragraph(data["summary"], body_style))
            elements.append(Spacer(1, 6))

        # Skills
        skills = data.get("skills", [])
        if skills:
            elements.append(Paragraph("TECHNICAL SKILLS", section_style))
            skill_text = ", ".join(s if isinstance(s, str) else s.get("name", "") for s in skills)
            elements.append(Paragraph(skill_text, body_style))
            elements.append(Spacer(1, 6))

        # Experience
        experiences = data.get("experience", [])
        if experiences:
            elements.append(Paragraph("PROFESSIONAL EXPERIENCE", section_style))
            for exp in experiences:
                role = exp.get("role", "Role")
                comp = exp.get("company", "Company")
                period = exp.get("period", "")
                header = f"<b>{role}</b> — {comp} <i>({period})</i>" if period else f"<b>{role}</b> — {comp}"
                elements.append(Paragraph(header, body_style))
                desc = exp.get("description", "")
                if isinstance(desc, list):
                    for bullet in desc:
                        elements.append(Paragraph(f"• {bullet}", bullet_style))
                elif desc:
                    elements.append(Paragraph(desc, bullet_style))
                elements.append(Spacer(1, 4))

        # Projects
        projects = data.get("projects", [])
        if projects:
            elements.append(Paragraph("PROJECTS", section_style))
            for proj in projects:
                pname = proj.get("name", "Project")
                tech = proj.get("technologies", [])
                tech_str = f" <i>({', '.join(tech)})</i>" if tech else ""
                elements.append(Paragraph(f"<b>{pname}</b>{tech_str}", body_style))
                desc = proj.get("description", "")
                if isinstance(desc, list):
                    for bullet in desc:
                        elements.append(Paragraph(f"• {bullet}", bullet_style))
                elif desc:
                    elements.append(Paragraph(desc, bullet_style))
                elements.append(Spacer(1, 4))

        # Education
        education = data.get("education", [])
        if education:
            elements.append(Paragraph("EDUCATION", section_style))
            for edu in education:
                degree = edu.get("degree", "Degree")
                inst = edu.get("institution", "Institution")
                year = edu.get("year", "")
                elements.append(Paragraph(f"<b>{degree}</b>, {inst} {f'({year})' if year else ''}", body_style))
                elements.append(Spacer(1, 2))

        doc.build(elements)
        return output_path

    @staticmethod
    def generate_cover_letter_pdf(
        candidate_info: Dict[str, Any],
        job_info: Dict[str, Any],
        letter_body: str,
        output_path: str
    ) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "NameHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1A202C"),
        )
        meta_style = ParagraphStyle(
            "Meta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=16,
            textColor=colors.HexColor("#2D3748"),
            spaceBefore=10,
        )

        elements = []
        name = candidate_info.get("full_name", "Candidate")
        elements.append(Paragraph(name, title_style))
        email = candidate_info.get("email", "")
        phone = candidate_info.get("phone", "")
        loc = candidate_info.get("location", "")
        elements.append(Paragraph(f"{email} | {phone} | {loc}", meta_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceBefore=4, spaceAfter=14))

        # Recipient Info
        company = job_info.get("company", "Hiring Team")
        role = job_info.get("title", "Position")
        elements.append(Paragraph(f"To: The Hiring Team at {company}", meta_style))
        elements.append(Paragraph(f"Re: Application for {role}", meta_style))
        elements.append(Spacer(1, 14))

        # Letter paragraphs
        for paragraph in letter_body.split("\n\n"):
            if paragraph.strip():
                elements.append(Paragraph(paragraph.strip(), body_style))

        elements.append(Spacer(1, 16))
        elements.append(Paragraph("Sincerely,", body_style))
        elements.append(Paragraph(f"<b>{name}</b>", body_style))

        doc.build(elements)
        return output_path

pdf_service = PDFService()
