from typing import List

from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.cover_letter import CoverLetterTemplate
from app.repositories.cover_letter_repo import CoverLetterRepository
from app.repositories.profile_repo import ProfileRepository
from app.schemas.cover_letter import CoverLetterCreate, CoverLetterUpdate
from app.schemas.profile import ProfileData


class IdentityService:
    def __init__(self, profile_repo: ProfileRepository, cover_repo: CoverLetterRepository):
        self.profile_repo = profile_repo
        self.cover_repo = cover_repo

    async def get_profile(self, user_id: int) -> ProfileData:
        profile = await self.profile_repo.get_for_user(user_id)
        return ProfileData.model_validate(profile, from_attributes=True) if profile else ProfileData()

    async def save_profile(self, user_id: int, data: ProfileData):
        return await self.profile_repo.upsert(user_id, data)

    async def list_templates(self, user_id: int) -> List[CoverLetterTemplate]:
        return await self.cover_repo.list_for_user(user_id)

    async def _owned(self, template_id: int, user_id: int) -> CoverLetterTemplate:
        template = await self.cover_repo.get(template_id)
        if not template:
            raise NotFoundException("Cover letter template not found.")
        if template.user_id != user_id:
            raise ForbiddenException()
        return template

    async def get_template(self, template_id: int, user_id: int) -> CoverLetterTemplate:
        return await self._owned(template_id, user_id)

    async def create_template(self, user_id: int, data: CoverLetterCreate) -> CoverLetterTemplate:
        if await self.cover_repo.get_by_name(user_id, data.name):
            raise ConflictException("You already have a template with this name.")
        if data.is_default:
            await self.cover_repo.clear_default(user_id)
        template = CoverLetterTemplate(user_id=user_id, name=data.name, body=data.body, is_default=data.is_default)
        return await self.cover_repo.save(template)

    async def update_template(self, template_id: int, user_id: int, data: CoverLetterUpdate) -> CoverLetterTemplate:
        template = await self._owned(template_id, user_id)
        if data.name is not None and data.name != template.name:
            if await self.cover_repo.get_by_name(user_id, data.name):
                raise ConflictException("You already have a template with this name.")
            template.name = data.name
        if data.body is not None:
            template.body = data.body
        if data.is_default is not None:
            if data.is_default:
                await self.cover_repo.clear_default(user_id)
            template.is_default = data.is_default
        return await self.cover_repo.save(template)

    async def delete_template(self, template_id: int, user_id: int) -> None:
        await self.cover_repo.delete(await self._owned(template_id, user_id))
