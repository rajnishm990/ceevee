from typing import Optional

from app.core.config import settings
from app.core.exceptions import FileTooLargeException, ForbiddenException, NotFoundException, UnsupportedFileException
from app.core.utils import generate_shareable_slug
from app.repositories.section_repo import SectionRepository
from app.repositories.version_repo import VersionRepository
from app.schemas.section import SectionCreate, SectionUpdate
from app.services import pdf_engine
from app.services.storage_service import StorageService


class ResumeService:
    

    def __init__(self, section_repo: SectionRepository, version_repo: VersionRepository):
        self.section_repo = section_repo
        self.version_repo = version_repo

    # # sections

    async def create_section(self, user_id: int, section_in: SectionCreate):
        slug = generate_shareable_slug(section_in.domain_name)
        while await self.section_repo.slug_exists(slug):
            slug = generate_shareable_slug(section_in.domain_name)
        return await self.section_repo.create(user_id, section_in, slug)

    async def get_owned_section(self, section_id: int, user_id: int, *, with_versions: bool = False):
        section = await self.section_repo.get_by_id(section_id, with_versions=with_versions)
        if not section:
            raise NotFoundException("Section not found.")
        if section.user_id != user_id:
            raise ForbiddenException()
        return section

    async def update_section(self, section_id: int, user_id: int, section_in: SectionUpdate):
        section = await self.get_owned_section(section_id, user_id)
        return await self.section_repo.update(section, section_in)

    async def delete_section(self, section_id: int, user_id: int) -> None:
        section = await self.get_owned_section(section_id, user_id)
        await self.section_repo.delete(section)

    async def set_active_version(self, section_id: int, user_id: int, version_id: int):
        section = await self.get_owned_section(section_id, user_id)
        version = await self.version_repo.get_by_id(version_id)
        if not version or version.section_id != section.id:
            raise NotFoundException("Version not found in this section.")
        return await self.section_repo.set_active_version(section, version_id)

    ## Versions

    async def upload_version(
        self, section_id: int, user_id: int, filename: str, raw_bytes: bytes, label: Optional[str] = None
    ):
        section = await self.get_owned_section(section_id, user_id)

        if not filename.lower().endswith(".pdf"):
            raise UnsupportedFileException()
        if len(raw_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise FileTooLargeException()

        layout = pdf_engine.extract_layout(raw_bytes)

        file_id = StorageService.new_file_id()
        stored_path = await StorageService.save_file(file_id, raw_bytes)

        version_number = await self.version_repo.count_for_section(section.id) + 1
        version = await self.version_repo.create(
            section_id=section.id,
            version_number=version_number,
            base_template_url=stored_path,
            coordinate_map=layout["coordinate_map"],
            content=layout["content"],
            label=label,
        )

        # First upload in a section becomes active automatically; after
        # that, the user picks explicitly via set_active_version.
        if section.active_version_id is None:
            await self.section_repo.set_active_version(section, version.id)

        return version

    async def get_owned_version(self, version_id: int, user_id: int):
        version = await self.version_repo.get_by_id(version_id)
        if not version:
            raise NotFoundException("Version not found.")
        await self.get_owned_section(version.section_id, user_id)  # ownership check
        return version

    async def edit_version(self, version_id: int, user_id: int, updated_content: dict):
        version = await self.get_owned_version(version_id, user_id)

        merged_content = {**version.content, **updated_content}
        base_bytes = await StorageService.get_file(version.base_template_url)
        rendered_bytes = pdf_engine.render_pdf(base_bytes, version.coordinate_map, merged_content)

        file_id = StorageService.new_file_id()
        stored_path = await StorageService.save_file(file_id, rendered_bytes)

        version = await self.version_repo.update_content(version, merged_content)
        version = await self.version_repo.update_final_pdf_url(version, stored_path)
        return version

    async def get_version_pdf_bytes(self, version_id: int, user_id: int) -> bytes:
        version = await self.get_owned_version(version_id, user_id)
        path = version.final_pdf_url or version.base_template_url
        return await StorageService.get_file(path)

    # Public (recruiter-facing) 

    async def get_public_pdf_by_slug(self, slug: str) -> bytes:
        section = await self.section_repo.get_by_slug(slug)
        if not section or not section.active_version_id:
            raise NotFoundException("This resume link isn't available.")
        version = await self.version_repo.get_by_id(section.active_version_id)
        if not version:
            raise NotFoundException("This resume link isn't available.")
        path = version.final_pdf_url or version.base_template_url
        return await StorageService.get_file(path)
