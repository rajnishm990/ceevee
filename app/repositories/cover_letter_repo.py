from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cover_letter import CoverLetterTemplate


class CoverLetterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: int) -> List[CoverLetterTemplate]:
        result = await self.session.execute(
            select(CoverLetterTemplate).where(CoverLetterTemplate.user_id == user_id).order_by(CoverLetterTemplate.id)
        )
        return list(result.scalars().all())

    async def get(self, template_id: int) -> Optional[CoverLetterTemplate]:
        result = await self.session.execute(select(CoverLetterTemplate).where(CoverLetterTemplate.id == template_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: int, name: str) -> Optional[CoverLetterTemplate]:
        result = await self.session.execute(
            select(CoverLetterTemplate).where(CoverLetterTemplate.user_id == user_id, CoverLetterTemplate.name == name)
        )
        return result.scalar_one_or_none()

    async def clear_default(self, user_id: int) -> None:
        await self.session.execute(
            update(CoverLetterTemplate).where(CoverLetterTemplate.user_id == user_id).values(is_default=False)
        )

    async def save(self, template: CoverLetterTemplate) -> CoverLetterTemplate:
        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)
        return template

    async def delete(self, template: CoverLetterTemplate) -> None:
        await self.session.delete(template)
        await self.session.flush()
