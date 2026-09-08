from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import select 
from app.models.version import ResumeVersion 
from app.schemas.version import ResumeVersionCreate 


class VersionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session 


    async def create(self , version_in: ResumeVersionCreate , base_template_path:str):
        db_obj =  ResumeVersion(
            section_id = version_in.section_id,
            base_template_url = base_template_path,
            coordinate_map = version_in.coordinate_map,
            content = version_in.content
        )

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj 

    async def get_by_id(self, version_id: int) -> ResumeVersion| None:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        result = await self.session.execute(smtm)
        return result.scalar_one_or_none()

    async def update_final_pdf_url(self, version_id : int , url:str) -> None:
        version = await self.get_by_id(version_id)
        if version:
            version.final_pdf_url = url 
            self.session.add(version)
            await self.session.flush()