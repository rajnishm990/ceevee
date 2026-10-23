from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.schemas.common import validate_http_url

# def _validate_http_url(value: Optional[str]) -> Optional[str]:
#     if value is None or value == "":
#         return None
#     value = value.strip()
#     parsed = urlparse(value)
#     if parsed.scheme not in ("http", "https") or not parsed.netloc:
#         raise ValueError("Must be a valid http(s) URL.")
#     if len(value) > 300:
#         raise ValueError("URL is too long.")
#     return value


class LinkItem(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    url: str

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        return validate_http_url(v) or ""


class FieldItem(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    value: str = Field(max_length=500)


class ProfileData(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=120)
    headline: Optional[str] = Field(default=None, max_length=160)
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=40)
    location: Optional[str] = Field(default=None, max_length=120)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    other_links: List[LinkItem] = Field(default_factory=list, max_length=10)
    custom_fields: List[FieldItem] = Field(default_factory=list, max_length=20)

    @field_validator("linkedin_url", "github_url", "website_url")
    @classmethod
    def _urls(cls, v: Optional[str]) -> Optional[str]:
        return validate_http_url(v)


class ProfileResponse(ProfileData):
    model_config = ConfigDict(from_attributes=True)
