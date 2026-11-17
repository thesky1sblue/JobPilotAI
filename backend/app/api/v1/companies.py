from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.jobs import Company

router = APIRouter()

@router.get("/")
async def list_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.is_in_watchlist == True))
    companies = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "domain": c.domain,
            "careers_url": c.careers_url,
            "ats_platform": c.ats_platform,
            "ats_identifier": c.ats_identifier,
            "location": c.location,
            "industry": c.industry,
            "is_verified": c.is_verified,
            "last_discovered_at": c.last_discovered_at.isoformat() if c.last_discovered_at else None,
        }
        for c in companies
    ]

@router.post("/seed")
async def seed_companies(db: AsyncSession = Depends(get_db)):
    from app.services.company_service import seed_initial_companies
    count = await seed_initial_companies(db)
    return {"seeded": count}

@router.post("/")
async def add_company(data: dict, db: AsyncSession = Depends(get_db)):
    from app.models.jobs import Company
    company = Company(**{k: v for k, v in data.items() if hasattr(Company, k)})
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return {"id": str(company.id), "name": company.name}
