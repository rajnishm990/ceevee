from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import get_resume_service
from app.core.config import settings
from app.core.rate_limit import limiter
from app.services.resume_service import ResumeService

router = APIRouter()


@router.get("/{slug}")
@limiter.limit(settings.RATE_LIMIT_PUBLIC_SHARE)
async def get_public_resume(request: Request, slug: str, service: ResumeService = Depends(get_resume_service)):
    """Recruiter-facing endpoint. No auth required (that's the point - it's
    the link you hand to a recruiter), but it still goes through the normal
    DB dependency rather than opening its own session, so it stays testable
    and consistent with every other endpoint. Deliberately returns ONLY the
    raw PDF - no JSON, no metadata, no hint of what else exists on the
    account."""
    pdf_bytes = await service.get_public_pdf_by_slug(slug)
    return Response(content=pdf_bytes, media_type="application/pdf")
