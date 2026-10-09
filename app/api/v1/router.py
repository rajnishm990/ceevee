from fastapi import APIRouter

from app.api.v1.endpoints import auth, public, sections, versions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(sections.router, prefix="/sections", tags=["sections"])
api_router.include_router(versions.router, tags=["versions"])  # paths already include /sections/{id}/versions
api_router.include_router(public.router, prefix="/public", tags=["public"])
