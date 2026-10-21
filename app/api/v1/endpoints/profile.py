from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_identity_service
from app.models.user import User
from app.schemas.profile import ProfileData, ProfileResponse
from app.services.identity_service import IdentityService

router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
):
    return await service.get_profile(current_user.id)


@router.put("", response_model=ProfileResponse)
async def save_profile(
    payload: ProfileData,
    current_user: User = Depends(get_current_user),
    service: IdentityService = Depends(get_identity_service),
):
    return await service.save_profile(current_user.id, payload)
