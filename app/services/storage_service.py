import asyncio
import os
import uuid
from functools import lru_cache

import aiofiles

from app.core.config import settings
from app.core.security import decrypt_pdf_payload, encrypt_pdf_payload

S3_PREFIX = "resumes/"


@lru_cache
def _s3_client(region: str, endpoint: str, key_id: str, secret: str):
    import boto3

    kwargs = {"region_name": region}
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    if key_id:
        kwargs.update(aws_access_key_id=key_id, aws_secret_access_key=secret)
    return boto3.client("s3", **kwargs)


def s3():
    return _s3_client(settings.S3_REGION, settings.S3_ENDPOINT_URL, settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)


class StorageService:
    @staticmethod
    def new_file_id() -> str:
        return uuid.uuid4().hex

    @staticmethod
    async def save_file(file_id: str, raw_bytes: bytes) -> str:
        data = encrypt_pdf_payload(raw_bytes)

        if settings.STORAGE_BACKEND == "local":
            os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
            path = os.path.join(settings.LOCAL_STORAGE_DIR, f"{file_id}.enc")
            async with aiofiles.open(path, "wb") as f:
                await f.write(data)
            return path

        key = f"{S3_PREFIX}{file_id}.enc"
        await asyncio.to_thread(
            s3().put_object, Bucket=settings.S3_BUCKET_NAME, Key=key, Body=data, ContentType="application/octet-stream"
        )
        return key

    @staticmethod
    async def get_file(path: str) -> bytes:
        if settings.STORAGE_BACKEND == "local":
            async with aiofiles.open(path, "rb") as f:
                return decrypt_pdf_payload(await f.read())

        def _read() -> bytes:
            return s3().get_object(Bucket=settings.S3_BUCKET_NAME, Key=path)["Body"].read()

        return decrypt_pdf_payload(await asyncio.to_thread(_read))

    @staticmethod
    async def delete_file(path: str) -> None:
        if settings.STORAGE_BACKEND == "local":
            if os.path.exists(path):
                os.remove(path)
            return
        await asyncio.to_thread(s3().delete_object, Bucket=settings.S3_BUCKET_NAME, Key=path)
