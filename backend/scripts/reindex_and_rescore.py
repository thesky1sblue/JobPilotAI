import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, delete
from app.models.jobs import Job, JobMatch, Company
from app.models.candidate import CandidateProfile, CandidateFact, JobPreference
from app.services.ingestion_service import ingest_resume
from app.agents.extraction import extract_skills_from_text, extract_experience, detect_location_type, clean_html
from app.agents.matching import matching_agent

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jobpilot_local.db")
SQLITE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

async def main():
    print("1. Connecting to database:", DB_PATH)
    engine = create_async_engine(SQLITE_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        # Step 1: Re-ingest resume with full keyword extraction
        resume_path = "/Users/akash/Documents/autojob/Akash_s_Resume_new.pdf"
        print("2. Re-ingesting resume with complete technical fact matrix...")
        ingest_res = await ingest_resume(resume_path, session)
        print(f"   Candidate: {ingest_res['name']} ({ingest_res['email']})")
        print(f"   Verified Skills Extracted: {ingest_res['skills_count']}")
        print(f"   Total Ground Truth Facts: {ingest_res['facts_count']}")

        # Fetch candidate profile & facts
        cand = (await session.execute(select(CandidateProfile).limit(1))).scalar_one()
        facts_res = await session.execute(select(CandidateFact).where(CandidateFact.candidate_id == cand.id))
        facts = [{"type": f.fact_type, "data": f.fact_data} for f in facts_res.scalars().all()]
        pref_res = await session.execute(select(JobPreference).where(JobPreference.candidate_id == cand.id))
        pref = pref_res.scalar_one_or_none()
        preferences = {
            "target_roles": pref.target_roles if pref else ["AI / ML Engineer", "Software Development / SDE", "Python Developer"],
            "preferred_locations": pref.preferred_locations if pref else ["Bangalore", "Chennai", "Remote", "Hyderabad"],
            "experience_years": 0.5,
        }

        # Step 2: Re-parse and Re-score all jobs
        print("3. Re-extracting and re-scoring all discovered jobs...")
        jobs_res = await session.execute(select(Job))
        jobs = jobs_res.scalars().all()
        print(f"   Found {len(jobs)} jobs to process.")

        # Clear old matches
        await session.execute(delete(JobMatch))

        strong_count = 0
        good_count = 0

        for i, job in enumerate(jobs):
            # Clean HTML description and extract richer skills
            clean_desc = clean_html(job.description or "")
            job.description = clean_desc
            combined_text = f"{job.title}\n{clean_desc}"
            job.required_skills = extract_skills_from_text(combined_text)
            job.experience_min = extract_experience(combined_text)
            job.location_type = detect_location_type(job.location or "")

            # Match
            match_res = await matching_agent.run({
                "job": {
                    "id": str(job.id),
                    "title": job.title,
                    "description": clean_desc,
                    "required_skills": job.required_skills,
                    "location": job.location,
                    "experience_min": job.experience_min,
                },
                "candidate_facts": facts,
                "preferences": preferences,
            })

            if match_res["status"] == "success":
                data = match_res["data"]
                match = JobMatch(
                    job_id=job.id,
                    candidate_id=cand.id,
                    overall_score=data["overall_score"],
                    skill_score=data["skill_score"],
                    role_score=data["role_score"],
                    experience_score=data["experience_score"],
                    location_score=data["location_score"],
                    salary_score=data["salary_score"],
                    education_score=data["education_score"],
                    matched_skills=data["matched_skills"],
                    missing_skills=data["missing_skills"],
                    explanation=data["explanation"],
                    is_eligible=data["is_eligible"],
                    classification=data["classification"],
                )
                session.add(match)
                if data["overall_score"] >= 80:
                    strong_count += 1
                elif data["overall_score"] >= 70:
                    good_count += 1

            if (i + 1) % 200 == 0:
                print(f"   Processed {i + 1}/{len(jobs)} jobs... ({strong_count} strong matches so far)")

        await session.commit()
        print(f"4. Re-scoring complete!")
        print(f"   Total Jobs: {len(jobs)}")
        print(f"   Strong Matches (>=80%): {strong_count}")
        print(f"   Good Matches (70-79%): {good_count}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
