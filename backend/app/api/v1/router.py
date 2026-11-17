from fastapi import APIRouter
from app.api.v1 import candidate, jobs, applications, companies
from app.api.v1 import settings as settings_router

api_router = APIRouter()
api_router.include_router(candidate.router, prefix="/candidate", tags=["Candidate"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(settings_router.router, prefix="/settings", tags=["Settings"])
