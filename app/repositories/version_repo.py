from typing import List, Optional

from sqlalchemy import func, select, update
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
        page_info: list,
        label: Optional[str] = None,
    ) -> ResumeVersion:
        db_obj = ResumeVersion(
            section_id=section_id,
            version_number=version_number,
            label=label,
            base_template_url=base_template_url,
            coordinate_map=coordinate_map,
            content=content,
            page_info=page_info,
        )
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, version_id: int) -> Optional[ResumeVersion]:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        result = await self.session.execute(stmt)  
        return result.scalar_one_or_none()

    async def list_for_section(self, section_id: int) -> List[ResumeVersion]:
        result = await self.session.execute(
            select(ResumeVersion).where(ResumeVersion.section_id == section_id).order_by(ResumeVersion.version_number)
        )
        return list(result.scalars().all())

    async def count_for_section(self, section_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(ResumeVersion).where(ResumeVersion.section_id ==section_id)
        )
        return result.scalar_one()

    async def next_version_number(self, section_id: int) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.max(ResumeVersion.version_number), 0)).where(ResumeVersion.section_id == section_id)
        )
        return result.scalar_one() + 1

    async def update_label(self, version: ResumeVersion, label) -> ResumeVersion:
        version.label = label
        self.session.add(version)
        await self.session.flush()
        await self.session.refresh(version)
        return version

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

    async def save_edit(self, version: ResumeVersion, expected_revision: int, content: dict, final_pdf_url: str) -> bool:
        result = await self.session.execute(
            update(ResumeVersion)
            .where(ResumeVersion.id == version.id, ResumeVersion.revision == expected_revision)
            .values(content=content, final_pdf_url=final_pdf_url, revision=ResumeVersion.revision + 1)
        )
        if result.rowcount != 1:
            return False
        await self.session.refresh(version)
        return True
