from fastapi import APIRouter 

from app.core.config import settings 

router = APIRouter()

@router.get("/limits")
async def get_limits():
    return {
        "max_sections": settings.MAX_SECTIONS_PER_USER,
        "max_version_per_section": settings.MAX_VERSIONS_PER_SECTION,
        "max_upload_bytes": settings.MAX_UPLOAD_SIZE_BYTES,
    }

