# Project Context: ceevee

## Project Structure
```text
ceevee/
    alembic/
        env.py
        versions.py
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

```

---
### File: alembic\versions.py
**Path:** `alembic\versions.py`

```py

```

---
### File: app\main.py
**Path:** `app\main.py`

```py

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
```

---
### File: app\core\exceptions.py
**Path:** `app\core\exceptions.py`

```py

```

---
### File: app\core\rate_limit.py
**Path:** `app\core\rate_limit.py`

```py
from slowapi import Limiter 
from slowapi.util import get_remote_address
from app.core.config import settings 

limiter  = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    strategy="moving-window",
    default_limits=["100/minute"]

)


```

---
### File: app\core\security.py
**Path:** `app\core\security.py`

```py
import base64 
import os 
from datetime import datetime , timedelta , timezone 
from typing import Any , Dict , Tuple 
from argon2 import PasswordHasher 
from argon2.exceptions import VerifyMismatchError 
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import jwt 

from app.core.config import settings 

pwd_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,   #64 mb 
    parallelism=4,
    hash_len=32,
    salt_len=16
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


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def encrypt_pdf_payload(data: bytes) -> bytes:
    """
    Encrypts a raw PDF binary using AES-256-GCM.
    Returns: 12-byte Nonce + Ciphertext (which includes the 16-byte GCM authentication tag).
    """
    nonce = os.urandom(12)  # Standard 96-bit nonce for GCM
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
from typing import List , Optional 
from sqlalchemy import String , Integer , ForeignKey 
from sqlalchemy.orm import Mapped , mapped_column, relationship 
from app.db.base import BaseModel 

class ResumeSection(BaseModel):
    __tablename__ = "resume_sections" 

    id : Mapped[int] = mapped_column(primary_key=True , index=True)
    user_id = Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable= False
    )

    domain_name: Mapped[str] = mapped_column(String(50), nullable=False)  #backend , frontend etc 

    # Public slug for the recruiter (e.g., "alex-backend-49df")
    shareable_slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    
    # External backup link (Google Drive / Dropbox)
    gdrive_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Pointer to the currently active compiled version
    active_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("resume_versions.id", ondelete="SET NULL", use_alter=True, name="fk_section_active_version"),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sections")
    
    versions: Mapped[List["ResumeVersion"]] = relationship(
        "ResumeVersion", 
        back_populates="section",
        foreign_keys="ResumeVersion.section_id",
        cascade="all, delete-orphan"
    )
    
    active_version: Mapped[Optional["ResumeVersion"]] = relationship(
        "ResumeVersion",
        foreign_keys=[active_version_id],
        post_update=True
    )
```

---
### File: app\models\user.py
**Path:** `app\models\user.py`

```py
from typing import List , Dict , ANy , Optional 
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
from typing import Dict , Any , Optional 
from sqlalchemy import String , Integer , ForeignKey, JSON 
from sqlalchemy.orm import Mapped , mapped_column , relationship 
from app.db.base import BaseModel 


class ResumeVersion(BaseModel):
    __tablename__ = "resume_version"

    id: Mapped = mapped_column(primary_key=True , index=True)

    section_id: Mapped = mapped_column(
        ForeignKey("resume_sections.id", ondelete="CASCADE"),
        index=True ,
        nullable=False
    )

    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # e.g., "Tailored for Stripe Backend JD"

    # Storage paths for encrypted binary payloads (AES-256-GCM)
    base_template_url: Mapped[str] = mapped_column(String(500), nullable=False)
    final_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Core Parser Metadata
    coordinate_map: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    content: Mapped[Dict[str, str]] = mapped_column(JSON, nullable=False)

    # Relationships
    section: Mapped["ResumeSection"] = relationship(
        "ResumeSection", 
        back_populates="versions",
        foreign_keys=[section_id]
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

```

---
### File: app\repositories\user_repo.py
**Path:** `app\repositories\user_repo.py`

```py

```

---
### File: app\repositories\version_repo.py
**Path:** `app\repositories\version_repo.py`

```py
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

```

---
### File: app\schemas\user.py
**Path:** `app\schemas\user.py`

```py

```

---
### File: app\schemas\version.py
**Path:** `app\schemas\version.py`

```py
from pydantic import BaseModel , ConfigDict 
from typing import Dict , Any , Optional 
from datetime import datetime 


class ResumeVersionBase(BaseModel):
    content: Dict[str,str]

class ResumeVersionCreate(ResumeVersionBase):
    section_id = int 
    coordinate_map = Dict[str,Any]

class ResumeVersionResponse(ResumeVersionBase):
    id:int 
    section_id = int 
    created_at = datetime 

    #reads from sqlAlchemy directly
    model_config = ConfigDict(from_attributes=True)

class ResumeEditRequest(BaseModel):
    updated_content: Dict[str, str]


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

```

---
### File: app\services\pdf_engine.py
**Path:** `app\services\pdf_engine.py`

```py

```

---
### File: app\services\resume_service.py
**Path:** `app\services\resume_service.py`

```py

```

---
### File: app\services\storage_service.py
**Path:** `app\services\storage_service.py`

```py
import os 
import aiofiles 
from app.core.config import settings 
from app.core.security import encrypt_pdf_payload , decrypt_pdf_payload 

class StorageService:
    @staticmethod
    async def save_file(file_id: str , raw_bytes:bytes) -> str:
        """  encrypts and writes the file and returns storage path / key """
        encrypted_data = encrypt_pdf_payload(raw_bytes)

        if settings.STORAGE_BACKEND == "local":
            os.makedirs(settings.LOCAL_STORAGE_DIR , exist_ok=True)
            path = os.path.join(settings.LOCAL_STORAGE_DIR , f"{file_id}.enc")

            async with aiofiles.open(path,"wb") as f:
                await f.write(encrypted_data)
            return path 

        elif settings.STORAGE_BACKEND == "s3":
            ## will add this later 
            pass

    @staticmethod 
    async def get_file(path:str ) -> bytes:
        """ gets and decrypt the file  """ 
        if settings.STORAGE_BACKEND == "local":
            async with aiofiles.open(path,'rb') as f :
                encrypted_data  = await f.read()
            return decrypt_pdf_payload(encrypted_data)

        elif settings.STORAGE_BACKEND == "s3":
            pass 

        
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

```

---
### File: tests\integration\test_auth_api.py
**Path:** `tests\integration\test_auth_api.py`

```py

```

---
### File: tests\integration\test_resume_flow.py
**Path:** `tests\integration\test_resume_flow.py`

```py

```

---
### File: tests\unit\test_pdf_engine.py
**Path:** `tests\unit\test_pdf_engine.py`

```py

```

---
### File: tests\unit\test_security.py
**Path:** `tests\unit\test_security.py`

```py

```

---
