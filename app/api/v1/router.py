from fastapi import APIRouter

from app.api.v1.endpoints import auth, cover_letters, profile, public, sections, versions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(cover_letters.router, prefix="/cover-letters", tags=["cover-letters"])
api_router.include_router(sections.router, prefix="/sections", tags=["sections"])
api_router.include_router(versions.router, tags=["versions"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
