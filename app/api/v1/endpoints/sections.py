from typing import List

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_resume_service
from app.models.user import User
from app.schemas.section import (
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    SectionWithVersions,
    SetActiveVersionRequest,
)
from app.services.resume_service import ResumeService

router = APIRouter()


@router.post("", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    payload: SectionCreate,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.create_section(current_user.id, payload)


@router.get("", response_model=List[SectionWithVersions])
async def list_sections(
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.section_repo.list_for_user(current_user.id)


@router.get("/{section_id}", response_model=SectionWithVersions)
async def get_section(
    section_id: int,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.get_owned_section(section_id, current_user.id, with_versions=True)


@router.patch("/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: int,
    payload: SectionUpdate,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.update_section(section_id, current_user.id, payload)


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section_id: int,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    await service.delete_section(section_id, current_user.id)


@router.post("/{section_id}/active-version", response_model=SectionResponse)
async def set_active_version(
    section_id: int,
    payload: SetActiveVersionRequest,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
):
    return await service.set_active_version(section_id, current_user.id, payload.version_id)
