# Project Context: ceevee

## Project Structure
```text
ceevee/
    alembic/
        env.py
        versions/
    app/
        main.py
        __init__.py
        api/
            deps.py
            __init__.py
            v1/
                router.py
                __init__.py
                endpoints/
                    auth.py
                    public.py
                    sections.py
                    versions.py
        core/
            config.py
            exceptions.py
            rate_limit.py
            security.py
            utils.py
            __init__.py
        db/
            base.py
            session.py
            __init__.py
        models/
            section.py
            user.py
            version.py
            __init__.py
        repositories/
            section_repo.py
            user_repo.py
            version_repo.py
            __init__.py
        schemas/
            section.py
            user.py
            version.py
            __init__.py
        services/
            auth_service.py
            pdf_engine.py
            resume_service.py
            storage_service.py
            __init__.py
    local_storage/
    tests/
        conftest.py
        integration/
            test_auth_api.py
            test_resume_flow.py
        unit/
            test_pdf_engine.py
            test_security.py
```

---

## File Contents

### File: alembic\env.py
**Path:** `alembic\env.py`

```py
import asyncio 
from logging.config import fileConfig 

from alembic import context 
from sqlalchemy import pool 
from sqlalchemy.engine import Connection 
from sqlalchemy.ext.asyncio import async_engine_from_config 

from app.core.config import settings 
from app.db.base import BaseModel 
from app.models import ResumeSection, ResumeVersion, User  

config = context.config 
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL) 

if config.config_file_name  is not None :
    fileConfig(config.config_file_name)

target_metadata = BaseModel.metadata 

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url , target_metadata=target_metadata , literal_binds=True )
    with context.begin_transaction():
        context.run_migrations() 

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass = pool.NullPool, 
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online)

```

---
### File: app\main.py
**Path:** `app\main.py`

```py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.base import BaseModel
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "local":
        # Quick local bootstrap so you're not forced into Alembic for a
        # throwaway dev DB. Production always goes through real migrations
        # (see alembic/env.py) - this block only ever runs for ENVIRONMENT=local.
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}

```

---
### File: app\__init__.py
**Path:** `app\__init__.py`

```py

```

---
### File: app\api\deps.py
**Path:** `app\api\deps.py`

```py
from fastapi import Depends 
from fastapi.security import OAuth2PasswordBearer 
from sqlalchemy.ext.asyncio import AsyncSession 
from app.core.exceptions import InvalidCredentialsException 
from app.core.security import decode_token 
from app.models.user import User  
from app.db.session import get_db 
from app.repositories.user_repo import UserRepository 
from app.repositories.section_repo import SectionRepository 
from app.repositories.version_repo import VersionRepository 
from app.services.resume_service import ResumeService 


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")  #token url is only for populating OpenAPi docs , login itself takes Json , not a form 


async def get_current_user(token: str = Depends(oauth2_scheme), db:AsyncSession = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise InvalidCredentialsException("Invalid or expired token") from exc 

    if payload.get["type"] != "access":
        raise InvalidCredentialsException("This is not an access token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(payload["sub"]))
    if not user or not user.is_active:
        raise InvalidCredentialsException()
    return user 

def get_user_repo(db:AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_resume_service(db: AsyncSession = Depends(get_db)) -> ResumeService:
    return ResumeService(SectionRepository(db), VersionRepository(db))

```

---
### File: app\api\__init__.py
**Path:** `app\api\__init__.py`

```py

```

---
### File: app\api\v1\router.py
**Path:** `app\api\v1\router.py`

```py

```

---
### File: app\api\v1\__init__.py
**Path:** `app\api\v1\__init__.py`

```py

```

---
### File: app\api\v1\endpoints\auth.py
**Path:** `app\api\v1\endpoints\auth.py`

```py
from fastapi import APIRouter , Depends, Request 

from app.api.deps import get_user_repo 
from app.core.rate_limit import limiter 
from app.repositories.user_repo import UserRepository 
from app.schemas.user import RefreshRequest,TokenPair,UserCreate, UserLogin , UserResponse 
from app.services.auth_service import AuthService
```

---
### File: app\api\v1\endpoints\public.py
**Path:** `app\api\v1\endpoints\public.py`

```py

```

---
### File: app\api\v1\endpoints\sections.py
**Path:** `app\api\v1\endpoints\sections.py`

```py

```

---
### File: app\api\v1\endpoints\versions.py
**Path:** `app\api\v1\endpoints\versions.py`

```py

```

---
### File: app\core\config.py
**Path:** `app\core\config.py`

```py
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

```

---
### File: app\core\exceptions.py
**Path:** `app\core\exceptions.py`

```py
from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "You do not have access to this resource."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "This resource already exists."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidCredentialsException(HTTPException):
    def __init__(self, detail: str = "Incorrect email or password."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UnsupportedFileException(HTTPException):
    def __init__(self, detail: str = "Only PDF files are supported."):
        super().__init__(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=detail)


class FileTooLargeException(HTTPException):
    def __init__(self, detail: str = "File exceeds the maximum upload size."):
        super().__init__(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=detail)

```

---
### File: app\core\rate_limit.py
**Path:** `app\core\rate_limit.py`

```py
from slowapi import Limiter 
from slowapi.util import get_remote_address
from app.core.config import settings 

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    strategy="moving-window",
    default_limits=[settings.RATE_LIMIT_DEFAULT],
)


```

---
### File: app\core\security.py
**Path:** `app\core\security.py`

```py
import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

pwd_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

_raw_enc_key = base64.b64decode(settings.PDF_ENCRYPTION_KEY)
aesgcm = AESGCM(_raw_enc_key)


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(subject: str | int, claims: Dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(subject), "exp": expire, "type": "access"}
    if claims:
        to_encode.update(claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(subject), "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def encrypt_pdf_payload(data: bytes) -> bytes:
    """
    Encrypts a raw PDF binary using AES-256-GCM.
    Returns: 12-byte nonce + ciphertext (which includes the 16-byte GCM auth tag).
    """
    nonce = os.urandom(12)  # standard 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext


def decrypt_pdf_payload(payload: bytes) -> bytes:
    """
    Splits the 12-byte nonce from the encrypted stream and decrypts the payload.
    Raises InvalidTag if data was altered or tampered with.
    """
    if len(payload) < 28:  # 12 bytes nonce + 16 bytes tag minimum
        raise ValueError("Corrupted encrypted payload: buffer too short.")
    nonce = payload[:12]
    ciphertext = payload[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)

```

---
### File: app\core\utils.py
**Path:** `app\core\utils.py`

```py
import re
import secrets


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def generate_shareable_slug(domain_name: str) -> str:
    """e.g. 'Backend' -> 'backend-x7fQ2a'. Collision handling (retry-until-unique)
    lives in ResumeService, since only it can check the DB."""
    return f"{slugify(domain_name)}-{secrets.token_urlsafe(5)}"

```

---
### File: app\core\__init__.py
**Path:** `app\core\__init__.py`

```py

```

---
### File: app\db\base.py
**Path:** `app\db\base.py`

```py
from datetime import datetime , timezone 

from sqlalchemy import DateTime 
from sqlalchemy.orm import DeclarativeBase , Mapped , declared_attr , mapped_column 



class BaseModel(DeclarativeBase):
    """ abstract base calss for all models , generates tables and standards like timestamps """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    # timezone aware timestamp 
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False 
    )
    updated_at: Mapped[DateTime]= mapped_column(
        DateTime(timezone=True),
        default= lambda : datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable= False 
    )
```

---
### File: app\db\session.py
**Path:** `app\db\session.py`

```py
from typing import AsyncGenerator 

from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker, async_session ,create_async_engine 

from app.core.config import settings 


engine = create_async_engine(
    settings.DATABASE_URL ,
    echo = settings.DEBUG ,
    future = True 
)

AsynSessionLocal = async_sessionmaker(
    bind = engine,
    class_ = AsyncSession ,
    expire_on_commit=False 

)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsynSessionLocal() as session:
        try:
            yield session 
            await session.commit 
        except Exception:
            await session.rollback()
            raise 


```

---
### File: app\db\__init__.py
**Path:** `app\db\__init__.py`

```py

```

---
### File: app\models\section.py
**Path:** `app\models\section.py`

```py
from typing import List, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class ResumeSection(BaseModel):
    __tablename__ = "resume_sections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    domain_name: Mapped[str] = mapped_column(String(50), nullable=False)  # "backend", "frontend", ...

    # Public slug for the recruiter (e.g. "backend-x7fQ2a"). This never
    # changes even as versions come and go - it always resolves to
    # whichever version is currently active.
    shareable_slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # Purely informational - has nothing to do with our storage/pipeline.
    gdrive_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    active_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("resume_versions.id", ondelete="SET NULL", use_alter=True, name="fk_section_active_version"),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="sections")

    versions: Mapped[List["ResumeVersion"]] = relationship(
        "ResumeVersion",
        back_populates="section",
        foreign_keys="ResumeVersion.section_id",
        cascade="all, delete-orphan",
    )

    active_version: Mapped[Optional["ResumeVersion"]] = relationship(
        "ResumeVersion",
        foreign_keys=[active_version_id],
        post_update=True,
    )
```

---
### File: app\models\user.py
**Path:** `app\models\user.py`

```py
from typing import List , Dict , Any , Optional 
from sqlalchemy import String , Boolean , JSON 
from sqlalchemy.orm import mapped_column , Mapped , relationship 
from app.db.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Master resume data: Work experience, projects, skills.
    # Stored as standard JSON (supported in SQLite & auto-promoted to JSONB in Postgres).
    base_profile: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # One User -> Many ResumeSections (e.g., Backend, Frontend, AI)
    sections: Mapped[List["ResumeSection"]] = relationship(
        "ResumeSection", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
```

---
### File: app\models\version.py
**Path:** `app\models\version.py`

```py
from typing import Any, Dict, Optional

from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class ResumeVersion(BaseModel):
    # NOTE: this must be "resume_versions" (plural) - ResumeSection's FK
    # points at "resume_versions.id". The original stub had this as
    # "resume_version" (singular), which would fail at table-creation time.
    __tablename__ = "resume_versions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    section_id: Mapped[int] = mapped_column(
        ForeignKey("resume_sections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g. "Tailored for Stripe"

    # Encrypted-at-rest storage paths/keys (see StorageService). base_ is the
    # untouched original upload; final_ is the most recently rendered edit.
    base_template_url: Mapped[str] = mapped_column(String(500), nullable=False)
    final_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # span_id -> {page, bbox, font, size, color} - the "skeleton" of the PDF.
    coordinate_map: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    # span_id -> current text - what the edit UI actually reads/writes.
    content: Mapped[Dict[str, str]] = mapped_column(JSON, nullable=False)

    section: Mapped["ResumeSection"] = relationship(
        "ResumeSection",
        back_populates="versions",
        foreign_keys=[section_id],
    )

```

---
### File: app\models\__init__.py
**Path:** `app\models\__init__.py`

```py
from app.db.base import BaseModel 
from app.models.user import User 
from app.models.version import ResumeVersion 
from app.models.section import ResumeSection 

__all__ = ["BaseModel", "User", "ResumeSection", "ResumeVersion"]
```

---
### File: app\repositories\section_repo.py
**Path:** `app\repositories\section_repo.py`

```py
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.section import ResumeSection
from app.schemas.section import SectionCreate, SectionUpdate


class SectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, section_in: SectionCreate, shareable_slug: str) -> ResumeSection:
        db_obj = ResumeSection(
            user_id=user_id,
            domain_name=section_in.domain_name,
            gdrive_link=section_in.gdrive_link,
            shareable_slug=shareable_slug,
        )
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, section_id: int, *, with_versions: bool = False) -> Optional[ResumeSection]:
        stmt = select(ResumeSection).where(ResumeSection.id == section_id)
        if with_versions:
            stmt = stmt.options(selectinload(ResumeSection.versions))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[ResumeSection]:
        result = await self.session.execute(select(ResumeSection).where(ResumeSection.shareable_slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        return (await self.get_by_slug(slug)) is not None

    async def list_for_user(self, user_id: int) -> List[ResumeSection]:
        result = await self.session.execute(
            select(ResumeSection).where(ResumeSection.user_id == user_id).options(selectinload(ResumeSection.versions))
        )
        return list(result.scalars().all())

    async def update(self, section: ResumeSection, section_in: SectionUpdate) -> ResumeSection:
        if section_in.domain_name is not None:
            section.domain_name = section_in.domain_name
        if section_in.gdrive_link is not None:
            section.gdrive_link = section_in.gdrive_link
        self.session.add(section)
        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def set_active_version(self, section: ResumeSection, version_id: int) -> ResumeSection:
        section.active_version_id = version_id
        self.session.add(section)
        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def delete(self, section: ResumeSection) -> None:
        await self.session.delete(section)
        await self.session.flush()

```

---
### File: app\repositories\user_repo.py
**Path:** `app\repositories\user_repo.py`

```py
from typing import Optional 
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 

from app.models.user import User 
from app.schemas.user import UserCreate 

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session 

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user_in: UserCreate, hashed_password: str) -> User:
        db_obj = User(email=user_in.email , hashed_password= hashed_password)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return  db_obj
```

---
### File: app\repositories\version_repo.py
**Path:** `app\repositories\version_repo.py`

```py
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

```

---
### File: app\repositories\__init__.py
**Path:** `app\repositories\__init__.py`

```py

```

---
### File: app\schemas\section.py
**Path:** `app\schemas\section.py`

```py
from typing import List , Optional 
from pydantic import BaseModel , ConfigDict , Field 
from app.schemas.version import VersionSummary 


class SectionCreate(BaseModel):
    domain_name : str = Field(min_length=1 , max_length=50)
    grive_link: Optional[str] = None 

class SectionUpdate(BaseModel):
    domain_name: Optional[str] = Field(default=None , min_length=1 , max_length=50)
    grive_link: Optional[str] = None  

class SetActiveVersionRequest(BaseModel):
    version_id: int 

class SectionResponse(BaseModel):
    id: int 
    domain_name: str 
    shareable_slug : str 
    grive_link : Optional[str]
    active_version_id: Optional[int]

    model_config= ConfigDict(from_attributes=True)

class SectionWithVersions(SectionResponse):
    versions : List[VersionSummary] = []
```

---
### File: app\schemas\user.py
**Path:** `app\schemas\user.py`

```py
from typing import Any , Dict 

from pydantic import BaseModel , ConfigDict , EmailStr , Field 


class UserCreate(BaseModel):
    email: EmailStr 
    password: str = Field(min_length=8 , max_length=128)

class UserLogin(BaseModel):
    email: EmailStr 
    password: str 

class UserResponse(BaseModel):
    id: int 
    email: EmailStr
    is_active = bool 
    base_profile: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class TokenPair(BaseModel):
    access_token : str 
    refresh_token : str 
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str 
```

---
### File: app\schemas\version.py
**Path:** `app\schemas\version.py`

```py
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class ResumeVersionResponse(BaseModel):
    id: int
    section_id: int
    version_number: int
    label: Optional[str]
    content: Dict[str, str]
    coordinate_map: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VersionSummary(BaseModel):
    """Lighter-weight shape used when listing versions inside a section."""

    id: int
    version_number: int
    label: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeEditRequest(BaseModel):
    # span_id -> new text. Only spans you include are changed; everything
    # else in the PDF stays pixel-identical.
    updated_content: Dict[str, str]


class LabelUpdateRequest(BaseModel):
    label: Optional[str] = None

```

---
### File: app\schemas\__init__.py
**Path:** `app\schemas\__init__.py`

```py

```

---
### File: app\services\auth_service.py
**Path:** `app\services\auth_service.py`

```py
from app.core.exceptions import ConflictException, InvalidCredentialsException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repo import UserRepository
from app.schemas.user import TokenPair, UserCreate


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, user_in: UserCreate):
        existing = await self.user_repo.get_by_email(user_in.email)
        if existing:
            raise ConflictException("An account with this email already exists.")
        hashed = hash_password(user_in.password)
        return await self.user_repo.create(user_in, hashed)

    async def authenticate(self, email: str, password: str) -> TokenPair:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise InvalidCredentialsException("Invalid or expired refresh token.") from exc

        if payload.get("type") != "refresh":
            raise InvalidCredentialsException("That isn't a refresh token.")

        user = await self.user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise InvalidCredentialsException()

        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

```

---
### File: app\services\pdf_engine.py
**Path:** `app\services\pdf_engine.py`

```py
from typing import Any, Dict, Tuple

import fitz  # PyMuPDF


def extract_layout(pdf_bytes: bytes) -> Dict[str, Any]:
    """Returns {"coordinate_map": {...}, "content": {...}}."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    coordinate_map: Dict[str, Any] = {}
    content: Dict[str, str] = {}

    try:
        span_counter = 0
        for page_index in range(len(doc)):
            page = doc[page_index]
            raw = page.get_text("dict")
            for block in raw["blocks"]:
                if block.get("type") != 0:  # 0 = text block, 1 = image block
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        if not text.strip():
                            continue
                        span_counter += 1
                        span_id = f"s{span_counter:04d}"
                        coordinate_map[span_id] = {
                            "page": page_index,
                            "bbox": list(span["bbox"]),
                            "font": span["font"],
                            "size": span["size"],
                            "color": span["color"],
                        }
                        content[span_id] = text
    finally:
        doc.close()

    return {"coordinate_map": coordinate_map, "content": content}


def render_pdf(base_pdf_bytes: bytes, coordinate_map: Dict[str, Any], content: Dict[str, str]) -> bytes:
    """Applies `content` on top of the ORIGINAL `base_pdf_bytes`, using the
    positions recorded in `coordinate_map`. Only spans present in `content`
    with different text than what's already there get touched."""
    doc = fitz.open(stream=base_pdf_bytes, filetype="pdf")
    try:
        pages_touched = set()
        spans_to_redraw = []

        for span_id, meta in coordinate_map.items():
            new_text = content.get(span_id)
            if new_text is None:
                continue
            page_index = meta["page"]
            rect = fitz.Rect(meta["bbox"])
            doc[page_index].add_redact_annot(rect, fill=(1, 1, 1))
            pages_touched.add(page_index)
            spans_to_redraw.append((span_id, meta, new_text))

        for page_index in pages_touched:
            doc[page_index].apply_redactions()

        for span_id, meta, new_text in spans_to_redraw:
            page = doc[meta["page"]]
            x0, y0, x1, y1 = meta["bbox"]
            box_width = x1 - x0
            box_height = y1 - y0
            original_size = meta["size"]
            fontsize = _fit_font_size(new_text, box_width, original_size)
            color = _unpack_color(meta["color"])
            # insert_text's point is the text baseline; approximate it as
            # sitting a little above the bottom of the original box.
            baseline_y = y1 - (box_height * 0.2)
            page.insert_text((x0, baseline_y), new_text, fontsize=fontsize, color=color, fontname="helv")

        return doc.tobytes(deflate=True, garbage=4)
    finally:
        doc.close()


def _unpack_color(color_int: int) -> Tuple[float, float, float]:
    """PyMuPDF packs RGB as a single int; unpack to the (r, g, b) 0-1 floats
    insert_text wants."""
    r = ((color_int >> 16) & 255) / 255
    g = ((color_int >> 8) & 255) / 255
    b = (color_int & 255) / 255
    return (r, g, b)


def _fit_font_size(text: str, box_width: float, original_size: float, min_size: float = 6.0) -> float:
    """Crude but effective v1 anti-overflow: shrink the font until the
    (estimated) text width fits the original box. 0.5 is a rough average
    glyph-width-to-fontsize ratio for Helvetica; good enough to avoid
    obvious overflow, not pixel-perfect kerning."""
    if not text:
        return original_size
    estimated_width = len(text) * original_size * 0.5
    if estimated_width <= box_width or original_size <= min_size:
        return original_size
    scale = box_width / estimated_width
    return max(min_size, original_size * scale)

```

---
### File: app\services\resume_service.py
**Path:** `app\services\resume_service.py`

```py
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

```

---
### File: app\services\storage_service.py
**Path:** `app\services\storage_service.py`

```py
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

```

---
### File: app\services\__init__.py
**Path:** `app\services\__init__.py`

```py

```

---
### File: tests\conftest.py
**Path:** `tests\conftest.py`

```py
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import BaseModel
from app.db.session import get_db
from app.main import app


@pytest.fixture(autouse=True)
def isolated_storage_dir(tmp_path: Path, monkeypatch):
    """Point encrypted PDF storage at a throwaway temp dir per test instead
    of the real local_storage/ folder, so running the suite doesn't leave
    files behind in the project."""
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path / "local_storage"))


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Each test gets a fresh in-memory SQLite DB - fast, isolated, no
    leftover state between tests, no need to touch the real ceevee_local.db."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with session_factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db] = _override_get_db

    async with session_factory() as session:
        yield session

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture()
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

```

---
### File: tests\integration\test_auth_api.py
**Path:** `tests\integration\test_auth_api.py`

```py
async def test_register_and_login(client):
    register_resp = await client.post(
        "/api/v1/auth/register", json={"email": "dev@example.com", "password": "supersecret123"}
    )
    assert register_resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": "dev@example.com", "password": "supersecret123"}
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_login_wrong_password_rejected(client):
    await client.post("/api/v1/auth/register", json={"email": "dev2@example.com", "password": "supersecret123"})
    resp = await client.post("/api/v1/auth/login", json={"email": "dev2@example.com", "password": "wrong-password"})
    assert resp.status_code == 401

```

---
### File: tests\integration\test_resume_flow.py
**Path:** `tests\integration\test_resume_flow.py`

```py
import fitz


def _tiny_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), text, fontsize=14)
    data = doc.tobytes()
    doc.close()
    return data


async def _auth_headers(client, email="flow@example.com", password="supersecret123"):
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_full_resume_flow(client):
    """Registers a user, creates a section, uploads a resume, edits it, and
    confirms the public share link serves the edited PDF - i.e. the whole
    loop this project is built around."""
    headers = await _auth_headers(client)

    section_resp = await client.post("/api/v1/sections", json={"domain_name": "backend"}, headers=headers)
    assert section_resp.status_code == 201
    section = section_resp.json()

    pdf_bytes = _tiny_pdf("Junior Backend Engineer")
    files = {"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    version_resp = await client.post(f"/api/v1/sections/{section['id']}/versions", files=files, headers=headers)
    assert version_resp.status_code == 201
    version = version_resp.json()

    span_id = next(iter(version["content"]))
    edit_resp = await client.patch(
        f"/api/v1/versions/{version['id']}",
        json={"updated_content": {span_id: "Senior Backend Engineer"}},
        headers=headers,
    )
    assert edit_resp.status_code == 200

    public_resp = await client.get(f"/api/v1/public/{section['shareable_slug']}")
    assert public_resp.status_code == 200
    assert public_resp.headers["content-type"] == "application/pdf"

    doc = fitz.open(stream=public_resp.content, filetype="pdf")
    text = doc[0].get_text()
    doc.close()
    assert "Senior Backend Engineer" in text

```

---
### File: tests\unit\test_pdf_engine.py
**Path:** `tests\unit\test_pdf_engine.py`

```py
import fitz

from app.services.pdf_engine import extract_layout, render_pdf


def _make_pdf_with_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), text, fontsize=14)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_extract_layout_finds_text_span():
    original = _make_pdf_with_text("Senior Backend Engineer")
    layout = extract_layout(original)
    assert list(layout["content"].values()) == ["Senior Backend Engineer"]
    assert len(layout["coordinate_map"]) == 1


def test_render_pdf_replaces_text_in_place():
    original = _make_pdf_with_text("Senior Backend Engineer")
    layout = extract_layout(original)
    span_id = next(iter(layout["content"]))
    edited_content = {span_id: "Staff Backend Engineer"}

    rendered = render_pdf(original, layout["coordinate_map"], edited_content)

    doc = fitz.open(stream=rendered, filetype="pdf")
    page_text = doc[0].get_text()
    doc.close()

    assert "Staff Backend Engineer" in page_text
    assert "Senior Backend Engineer" not in page_text

```

---
### File: tests\unit\test_security.py
**Path:** `tests\unit\test_security.py`

```py
from app.core.security import decrypt_pdf_payload, encrypt_pdf_payload, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_pdf_encryption_roundtrip():
    payload = b"%PDF-1.4 fake pdf bytes for testing"
    encrypted = encrypt_pdf_payload(payload)
    assert encrypted != payload
    assert decrypt_pdf_payload(encrypted) == payload

```

---
