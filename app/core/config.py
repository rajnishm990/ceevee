import base64
import os
from functools import lru_cache
from typing import List, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-only-secret-do-not-use-in-production"
DEV_PDF_ENCRYPTION_KEY = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="


class BaseAppSettings(BaseSettings):
    PROJECT_NAME: str = "ceevee"
    ENVIRONMENT: Literal["local", "production"] = "local"
    DEBUG: bool = False
    AUTO_MIGRATE: bool = False

    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    PDF_ENCRYPTION_KEY: str

    DATABASE_URL: str

    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = "./local_storage"
    S3_BUCKET_NAME: str = "resume-wallet-vault"
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    RATE_LIMIT_STORAGE_URI: str = "memory://"
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_PUBLIC_SHARE: str = "30/minute"

    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGIN_REGEX: str = r"^(http://localhost:\d+|http://127\.0\.0\.1:\d+|chrome-extension://.*)$"

    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024
    MAX_SECTIONS_PER_USER: int = 20
    MAX_VERSIONS_PER_SECTION: int = 20

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
    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8", extra="ignore")

    SECRET_KEY: str = DEV_SECRET_KEY
    PDF_ENCRYPTION_KEY: str = DEV_PDF_ENCRYPTION_KEY
    DATABASE_URL: str = "sqlite+aiosqlite:///./ceevee_local.db"
    DEBUG: bool = True
    AUTO_MIGRATE: bool = True


class ProductionSettings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=".env.production", env_file_encoding="utf-8", extra="ignore")

    STORAGE_BACKEND: Literal["local", "s3"] = "s3"
    ALLOWED_HOSTS: List[str]
    CORS_ORIGIN_REGEX: str

    @model_validator(mode="after")
    def reject_unsafe_production_config(self):
        problems = []
        if self.SECRET_KEY == DEV_SECRET_KEY or len(self.SECRET_KEY) < 32:
            problems.append("SECRET_KEY must be a unique value of at least 32 characters")
        if self.PDF_ENCRYPTION_KEY == DEV_PDF_ENCRYPTION_KEY:
            problems.append("PDF_ENCRYPTION_KEY must not be the development key")
        if "*" in self.ALLOWED_HOSTS:
            problems.append("ALLOWED_HOSTS must list real hostnames, not '*'")
        if self.DATABASE_URL.startswith("sqlite"):
            problems.append("DATABASE_URL must not be SQLite in production")
        if self.RATE_LIMIT_STORAGE_URI.startswith("memory"):
            problems.append("RATE_LIMIT_STORAGE_URI must be a shared store (e.g. redis://) in production")
        if self.DEBUG:
            problems.append("DEBUG must be false")
        if problems:
            raise ValueError("Unsafe production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> BaseAppSettings:
    if os.getenv("ENVIRONMENT", "local").lower() == "production":
        return ProductionSettings()
    return LocalSettings()


settings = get_settings()
