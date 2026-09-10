import base64
import os
from functools import lru_cache
from typing import List, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    PROJECT_NAME: str = "ceevee"
    ENVIRONMENT: Literal["local", "production"] = "local"
    DEBUG: bool = False

    # Auth
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    #  PDF at-rest encryption (AES-256-GCM)
    PDF_ENCRYPTION_KEY: str

    # Database
    DATABASE_URL: str

    # Storage backend
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = "./local_storage"
    S3_BUCKET_NAME: str = "resume-wallet-vault"
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Rate limiting (slowapi) 
    RATE_LIMIT_STORAGE_URI: str = "memory://"
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_PUBLIC_SHARE: str = "30/minute"

    # CORS 
    # Matches localhost (any port, for the website dev server) and any
    # chrome-extension:// origin (the extension's id changes per install).
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGIN_REGEX: str = r"^(http://localhost:\d+|http://127\.0\.0\.1:\d+|chrome-extension://.*)$"

    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB

    @field_validator("PDF_ENCRYPTION_KEY")
    @classmethod
    def validate_key_length(cls, v: str) -> str:
        try:
            decoded = base64.b64decode(v)
        except Exception as exc:
            raise ValueError("PDF_ENCRYPTION_KEY must be a valid base64 string.") from exc
        if len(decoded) != 32:
            raise ValueError("PDF_ENCRYPTION_KEY must decode to exactly 32 bytes.")
        return v


class LocalSettings(BaseAppSettings):
    """Zero external services: SQLite file, local disk folder, in-memory limiter."""

    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8", extra="ignore")
    SECRET_KEY: str = "dev-only-secret-do-not-use-in-production"
    PDF_ENCRYPTION_KEY: str = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
    DATABASE_URL: str = "sqlite+aiosqlite:///./ceevee_local.db"
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    DEBUG: bool = True


class ProductionSettings(BaseAppSettings):
    
    model_config = SettingsConfigDict(env_file=".env.production", env_file_encoding="utf-8", extra="ignore")

    STORAGE_BACKEND: Literal["local", "s3"] = "s3"
    DEBUG: bool = False


@lru_cache
def get_settings() -> BaseAppSettings:
    env = os.getenv("ENVIRONMENT", "local").lower()
    if env == "production":
        return ProductionSettings()
    return LocalSettings()


settings = get_settings()
