from fastapi import APIRouter

from app.api import health, jobs, projects

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(projects.router)
api_router.include_router(jobs.router)

__all__ = ["api_router"]
