from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.section import ResumeSection
from app.schemas.section import SectionCreate, SectionUpdate


class SectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, section_in: SectionCreate, shareable_slug: str) -> ResumeSection:
        db_obj = ResumeSection(
            user_id=user_id,
            domain_name=section_in.domain_name,
            gdrive_link=section_in.gdrive_link,
            shareable_slug=shareable_slug,
        )
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, section_id: int, *, with_versions: bool = False) -> Optional[ResumeSection]:
        stmt = select(ResumeSection).where(ResumeSection.id == section_id)
        if with_versions:
            stmt = stmt.options(selectinload(ResumeSection.versions))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[ResumeSection]:
        result = await self.session.execute(select(ResumeSection).where(ResumeSection.shareable_slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        return (await self.get_by_slug(slug)) is not None

    async def list_for_user(self, user_id: int) -> List[ResumeSection]:
        result = await self.session.execute(
            select(ResumeSection).where(ResumeSection.user_id == user_id).options(selectinload(ResumeSection.versions))
        )
        return list(result.scalars().all())

    async def update(self, section: ResumeSection, section_in: SectionUpdate) -> ResumeSection:
        if section_in.domain_name is not None:
            section.domain_name = section_in.domain_name
        if section_in.gdrive_link is not None:
            section.gdrive_link = section_in.gdrive_link
        self.session.add(section)
        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def set_active_version(self, section: ResumeSection, version_id: int) -> ResumeSection:
        section.active_version_id = version_id
        self.session.add(section)
        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def delete(self, section: ResumeSection) -> None:
        await self.session.delete(section)
        await self.session.flush()
