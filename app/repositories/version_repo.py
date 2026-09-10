from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.version import ResumeVersion


class VersionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        section_id: int,
        version_number: int,
        base_template_url: str,
        coordinate_map: dict,
        content: dict,
        label: Optional[str] = None,
    ) -> ResumeVersion:
        db_obj = ResumeVersion(
            section_id=section_id,
            version_number=version_number,
            label=label,
            base_template_url=base_template_url,
            coordinate_map=coordinate_map,
            content=content,
        )
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, version_id: int) -> Optional[ResumeVersion]:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        result = await self.session.execute(stmt)  # was "smtm" (typo'd) in the original stub
        return result.scalar_one_or_none()

    async def list_for_section(self, section_id: int) -> List[ResumeVersion]:
        result = await self.session.execute(
            select(ResumeVersion).where(ResumeVersion.section_id == section_id).order_by(ResumeVersion.version_number)
        )
        return list(result.scalars().all())

    async def count_for_section(self, section_id: int) -> int:
        return len(await self.list_for_section(section_id))

    async def update_final_pdf_url(self, version: ResumeVersion, url: str) -> ResumeVersion:
        version.final_pdf_url = url
        self.session.add(version)
        await self.session.flush()
        await self.session.refresh(version)
        return version

    async def update_content(self, version: ResumeVersion, content: dict) -> ResumeVersion:
        version.content = content
        self.session.add(version)
        await self.session.flush()
        await self.session.refresh(version)
        return version

    async def delete(self, version: ResumeVersion) -> None:
        await self.session.delete(version)
        await self.session.flush()
