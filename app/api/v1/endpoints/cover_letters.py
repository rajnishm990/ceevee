from typing import List

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_identity_service
from app.models.user import User
from app.schemas.cover_letter import CoverLetterCreate, CoverLetterResponse, CoverLetterUpdate
from app.services.identity_service import IdentityService

router = APIRouter()


@router.get("", response_model=List[CoverLetterResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
):
    return await service.list_templates(current_user.id)


@router.post("", response_model=CoverLetterResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: CoverLetterCreate,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
):
    return await service.create_template(current_user.id, payload)


@router.get("/{template_id}", response_model=CoverLetterResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
):
    return await service.get_template(template_id, current_user.id)


@router.patch("/{template_id}", response_model=CoverLetterResponse)
async def update_template(
    template_id: int,
    payload: CoverLetterUpdate,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
):
    return await service.update_template(template_id, current_user.id, payload)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
):
    await service.delete_template(template_id, current_user.id)
