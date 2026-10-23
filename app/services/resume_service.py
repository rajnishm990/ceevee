import asyncio
from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    FileTooLargeException,
    ForbiddenException,
    NotFoundException,
    UnsupportedFileException,
)
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

    async def _unique_slug(self, domain_name: str) -> str:
        slug = generate_shareable_slug(domain_name)
        while await self.section_repo.slug_exists(slug):
            slug = generate_shareable_slug(domain_name)
        return slug

    async def create_section(self, user_id: int, section_in: SectionCreate):
        if await self.section_repo.count_for_user(user_id) >= settings.MAX_SECTIONS_PER_USER:
            raise ConflictException(f"You can have at most {settings.MAX_SECTIONS_PER_USER} sections.")
        if await self.section_repo.get_by_user_and_name(user_id, section_in.domain_name):
            raise ConflictException("You already have a section with this name.")
        return await self.section_repo.create(user_id, section_in, await self._unique_slug(section_in.domain_name))

    async def rotate_slug(self, section_id: int, user_id: int):
        section = await self.get_owned_section(section_id, user_id)
        return await self.section_repo.set_slug(section, await self._unique_slug(section.domain_name))

    async def get_owned_section(self, section_id: int, user_id: int, *, with_versions: bool = False):
        section = await self.section_repo.get_by_id(section_id, with_versions=with_versions)
        if not section:
            raise NotFoundException("Section not found.")
        if section.user_id != user_id:
            raise ForbiddenException()
        return section

    async def update_section(self, section_id: int, user_id: int, section_in: SectionUpdate):
        section = await self.get_owned_section(section_id, user_id)
        new_name = section_in.domain_name
        if new_name and new_name.lower() != section.domain_name.lower():
            if await self.section_repo.get_by_user_and_name(user_id, new_name):
                raise ConflictException("You already have a section with this name.")
        return await self.section_repo.update(section, section_in)

    async def delete_section(self, section_id: int, user_id: int) -> None:
        section = await self.get_owned_section(section_id, user_id, with_versions=True)
        paths = self._paths_of(section.versions)
        await self.section_repo.delete(section)
        await self._delete_files(paths)

    async def set_active_version(self, section_id: int, user_id: int, version_id: int):
        section = await self.get_owned_section(section_id, user_id)
        version = await self.version_repo.get_by_id(version_id)
        if not version or version.section_id != section.id:
            raise NotFoundException("Version not found in this section.")
        return await self.section_repo.set_active_version(section, version_id)

    async def upload_version(
        self, section_id: int, user_id: int, filename: str, raw_bytes: bytes, label: Optional[str] = None
    ):
        section = await self.get_owned_section(section_id, user_id)

        if not filename.lower().endswith(".pdf") or not raw_bytes.startswith(b"%PDF-"):
            raise UnsupportedFileException()
        if len(raw_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise FileTooLargeException()
        if await self.version_repo.count_for_section(section.id) >= settings.MAX_VERSIONS_PER_SECTION:
            raise ConflictException(f"A section can hold at most {settings.MAX_VERSIONS_PER_SECTION} versions.")

        try:
            layout = await asyncio.to_thread(pdf_engine.extract_layout, raw_bytes)
        except pdf_engine.PdfReadError as exc:
            raise UnsupportedFileException(str(exc)) from exc

        stored_path = await StorageService.save_file(StorageService.new_file_id(), raw_bytes)
        version = await self.version_repo.create(
            section_id=section.id,
            version_number=await self.version_repo.next_version_number(section.id),
            base_template_url=stored_path,
            coordinate_map=layout["coordinate_map"],
            content=layout["content"],
            page_info=layout["page_info"],
            label=label,
        )
        if section.active_version_id is None:
            await self.section_repo.set_active_version(section, version.id)
        return version

    async def get_owned_version(self, version_id: int, user_id: int):
        version = await self.version_repo.get_by_id(version_id)
        if not version:
            raise NotFoundException("Version not found.")
        await self.get_owned_section(version.section_id, user_id)
        return version

    async def edit_version(self, version_id: int, user_id: int, updated_content: dict):
        version = await self.get_owned_version(version_id, user_id)

        unknown = set(updated_content) - set(version.coordinate_map)
        if unknown:
            raise BadRequestException(f"Unknown text ids: {sorted(unknown)[:5]}")

        merged = {**version.content, **updated_content}
        base_bytes = await StorageService.get_file(version.base_template_url)
        try:
            rendered = await asyncio.to_thread(pdf_engine.render_pdf, base_bytes, version.coordinate_map, merged)
        except pdf_engine.UnsupportedTextError as exc:
            raise BadRequestException(
                "These characters can't be drawn with this resume's fonts: " + " ".join(exc.chars)
            ) from exc

        old_final = version.final_pdf_url
        new_path = await StorageService.save_file(StorageService.new_file_id(), rendered)
        version = await self.version_repo.update_content(version, merged)
        version = await self.version_repo.update_final_pdf_url(version, new_path)
        if old_final:
            await self._delete_files([old_final])
        return version

    async def update_label(self, version_id: int, user_id: int, label: Optional[str]):
        version = await self.get_owned_version(version_id, user_id)
        return await self.version_repo.update_label(version, label)

    async def delete_version(self, version_id: int, user_id: int) -> None:
        version = await self.get_owned_version(version_id, user_id)
        section = await self.section_repo.get_by_id(version.section_id)
        if section.active_version_id == version.id:
            await self.section_repo.set_active_version(section, None)
        paths = self._paths_of([version])
        await self.version_repo.delete(version)
        await self._delete_files(paths)

    async def get_version_pdf_bytes(self, version_id: int, user_id: int, *, original: bool = False) -> bytes:
        version = await self.get_owned_version(version_id, user_id)
        path = version.base_template_url if original else (version.final_pdf_url or version.base_template_url)
        return await StorageService.get_file(path)

    async def get_active_pdf_bytes(self, section_id: int, user_id: int) -> bytes:
        section = await self.get_owned_section(section_id, user_id)
        return await self._pdf_for_active(section)

    async def get_public_pdf_by_slug(self, slug: str) -> bytes:
        section = await self.section_repo.get_by_slug(slug)
        if not section or not section.sharing_enabled:
            raise NotFoundException("This resume link isn't available.")
        return await self._pdf_for_active(section)

    async def _pdf_for_active(self, section) -> bytes:
        if not section.active_version_id:
            raise NotFoundException("This resume link isn't available.")
        version = await self.version_repo.get_by_id(section.active_version_id)
        if not version:
            raise NotFoundException("This resume link isn't available.")
        return await StorageService.get_file(version.final_pdf_url or version.base_template_url)

    @staticmethod
    def _paths_of(versions) -> List[str]:
        paths = []
        for v in versions:
            paths.append(v.base_template_url)
            if v.final_pdf_url:
                paths.append(v.final_pdf_url)
        return paths

    @staticmethod
    async def _delete_files(paths: List[str]) -> None:
        for path in paths:
            await StorageService.delete_file(path)
