import os
import uuid

import aiofiles

from app.core.config import settings
from app.core.security import decrypt_pdf_payload, encrypt_pdf_payload


class StorageService:
    

    @staticmethod
    def new_file_id() -> str:
        return uuid.uuid4().hex

    @staticmethod
    async def save_file(file_id: str, raw_bytes: bytes) -> str:
        encrypted_data = encrypt_pdf_payload(raw_bytes)

        if settings.STORAGE_BACKEND == "local":
            os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
            path = os.path.join(settings.LOCAL_STORAGE_DIR, f"{file_id}.enc")
            async with aiofiles.open(path, "wb") as f:
                await f.write(encrypted_data)
            return path

        if settings.STORAGE_BACKEND == "s3":
            raise NotImplementedError(
                "S3 storage backend isn't wired up yet - set STORAGE_BACKEND=local for now."
            )

        raise ValueError(f"Unknown STORAGE_BACKEND: {settings.STORAGE_BACKEND}")

    @staticmethod
    async def get_file(path: str) -> bytes:
        if settings.STORAGE_BACKEND == "local":
            async with aiofiles.open(path, "rb") as f:
                encrypted_data = await f.read()
            return decrypt_pdf_payload(encrypted_data)

        if settings.STORAGE_BACKEND == "s3":
            raise NotImplementedError(
                "S3 storage backend isn't wired up yet - set STORAGE_BACKEND=local for now."
            )

        raise ValueError(f"Unknown STORAGE_BACKEND: {settings.STORAGE_BACKEND}")

    @staticmethod
    async def delete_file(path: str) -> None:
        if settings.STORAGE_BACKEND == "local" and os.path.exists(path):
            os.remove(path)
