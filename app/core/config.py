from typing import List
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

    PROJECT_NAME: str = "Resume Wallet API"
    ENVIRONMENT: str = "production"  # local, staging, production
    DEBUG: bool = False

    # Security Keys
    SECRET_KEY: str                  
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
   
    PDF_ENCRYPTION_KEY: str          

    # Database & Cache
    DATABASE_URL: str                
    REDIS_URL: str                   

    # Storage Backend
    STORAGE_BACKEND: str = "s3"      # "s3" or "local"
    S3_BUCKET_NAME: str = "resume-wallet-vault"
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Security Guardrails
    ALLOWED_HOSTS: List[str] = ["*"]
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB strict limit
    
    @field_validator("PDF_ENCRYPTION_KEY")
    @classmethod
    def validate_key_length(cls, v: str) -> str:
        import base64
        try:
            decoded = base64.b64decode(v)
            if len(decoded) != 32:
                raise ValueError("PDF_ENCRYPTION_KEY must be a base64-encoded 32-byte key.")
        except Exception as exc:
            raise ValueError("Invalid Base64 string for PDF_ENCRYPTION_KEY.") from exc
        return v


settings = Settings()