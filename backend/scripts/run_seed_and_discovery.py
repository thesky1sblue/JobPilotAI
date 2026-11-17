import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models import *
from app.services.company_service import seed_initial_companies
from app.services.ingestion_service import ingest_resume
from app.services.discovery_service import run_discovery

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jobpilot_local.db")
SQLITE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

async def main():
    print("1. Creating database tables...")
    engine = create_async_engine(SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        print("2. Seeding initial companies...")
        seeded = await seed_initial_companies(session)
        print(f"   Seeded {seeded} watchlist companies.")

        print("3. Ingesting candidate resume...")
        resume_path = "/Users/akash/Documents/autojob/Akash_s_Resume_new.pdf"
        ingest_res = await ingest_resume(resume_path, session)
        print(f"   Candidate Profile: {ingest_res['name']} ({ingest_res['email']})")
        print(f"   Total Facts Ingested: {ingest_res['facts_count']}")

        print("4. Running discovery across Greenhouse & Lever boards...")
        discovery_res = await run_discovery(session)
        print(f"   Companies Scanned: {discovery_res['companies_scanned']}")
        print(f"   New Jobs Discovered & Matched: {discovery_res['new_jobs']}")

    await engine.dispose()
    print("ALL SEEDING & DISCOVERY TASKS COMPLETE.")

if __name__ == "__main__":
    asyncio.run(main())
