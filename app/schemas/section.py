from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import validate_http_url
from app.schemas.version import VersionSummary


class SectionCreate(BaseModel):
    domain_name: str = Field(min_length=1, max_length=50)
    gdrive_link: Optional[str] = None

    @field_validator("domain_name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be blank.")
        return v

    @field_validator("gdrive_link")
    @classmethod
    def _link(cls, v: Optional[str]) -> Optional[str]:
        return validate_http_url(v, max_length=500)


class SectionUpdate(BaseModel):
    domain_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    gdrive_link: Optional[str] = None
    sharing_enabled: Optional[bool] = None

    @field_validator("domain_name")
    @classmethod
    def _name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be blank.")
        return v

    @field_validator("gdrive_link")
    @classmethod
    def _link(cls, v: Optional[str]) -> Optional[str]:
        return validate_http_url(v, max_length=500)


class SetActiveVersionRequest(BaseModel):
    version_id: int


class SectionResponse(BaseModel):
    id: int
    domain_name: str
    shareable_slug: str
    gdrive_link: Optional[str]
    active_version_id: Optional[int]
    sharing_enabled: bool

    model_config = ConfigDict(from_attributes=True)


class SectionWithVersions(SectionResponse):
    versions: List[VersionSummary] = []
