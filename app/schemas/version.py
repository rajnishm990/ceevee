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
