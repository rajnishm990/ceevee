from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from app.api.deps import get_current_user, get_resume_service
from app.models.user import User
from app.schemas.version import ResumeEditRequest, ResumeVersionResponse
from app.services.resume_service import ResumeService

router = APIRouter()


@router.post(
    "/sections/{section_id}/versions",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_version(
    section_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    raw_bytes = await file.read()
    return await service.upload_version(section_id, current_user.id, file.filename, raw_bytes)


@router.patch("/versions/{version_id}", response_model=ResumeVersionResponse)
async def edit_version(
    version_id: int,
    payload: ResumeEditRequest,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.edit_version(version_id, current_user.id, payload.updated_content)


@router.get("/versions/{version_id}/download")
async def download_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    pdf_bytes = await service.get_version_pdf_bytes(version_id, current_user.id)
    return Response(content=pdf_bytes, media_type="application/pdf")
