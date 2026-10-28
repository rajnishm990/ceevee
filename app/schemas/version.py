from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResumeVersionResponse(BaseModel):
    id: int
    section_id: int
    version_number: int
    revision: int
    label: Optional[str]
    content: Dict[str, str]
    coordinate_map: Dict[str, Any]
    page_info: List[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VersionSummary(BaseModel):
    id: int
    version_number: int
    label: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeEditRequest(BaseModel):
    updated_content: Dict[str, str] = Field(max_length=2000)
    base_revision: Optional[int] = Field(default=None, ge=1)

    @field_validator("updated_content")
    @classmethod
    def _limit_text(cls, v: Dict[str, str]) -> Dict[str, str]:
        if any(len(t) > 500 for t in v.values()):
            raise ValueError("Each text span is limited to 500 characters.")
        return {k: " ".join(t.split("\n")).replace("\r", " ").replace("\t", " ") for k, t in v.items()}


class LabelUpdateRequest(BaseModel):
    label: Optional[str] = Field(default=None, max_length=100)

