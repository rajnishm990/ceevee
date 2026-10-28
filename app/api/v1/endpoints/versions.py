from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status , Request

from app.api.deps import get_current_user, get_resume_service
from app.api.responses import pdf_response
from app.core.config import settings
from app.models.user import User
from app.core.rate_limit import limiter
from app.schemas.version import LabelUpdateRequest, ResumeEditRequest, ResumeVersionResponse
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
    label: Optional[str] = Form(default=None, max_length=100),
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    raw_bytes = await file.read(settings.MAX_UPLOAD_SIZE_BYTES + 1)
    return await service.upload_version(section_id, current_user.id, file.filename or "", raw_bytes, label)


@router.get("/versions/{version_id}", response_model=ResumeVersionResponse)
async def get_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.get_owned_version(version_id, current_user.id)


@router.patch("/versions/{version_id}", response_model=ResumeVersionResponse)
async def edit_version(
    version_id: int,
    payload: ResumeEditRequest,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.edit_version(version_id, current_user.id, payload.updated_content)


@router.patch("/versions/{version_id}/label", response_model=ResumeVersionResponse)
async def update_label(
    version_id: int,
    payload: LabelUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.update_label(version_id, current_user.id, payload.label)


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    await service.delete_version(version_id, current_user.id)


@router.get("/versions/{version_id}/download")
async def download_version(
    version_id: int,
    source: Literal["current", "original"] = "current",
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    data = await service.get_version_pdf_bytes(version_id, current_user.id, original=source == "original")
    return pdf_response(data)


@router.post("/versions/{version_id}/preview")
@limiter.limit("60/minute")
async def preview_version(
    request: Request,
    version_id: int,
    payload: ResumeEditRequest,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return pdf_response(await service.preview_version(version_id, current_user.id, payload.updated_content))
