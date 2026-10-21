from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CoverLetterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=10000)
    is_default: bool = False


class CoverLetterUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    body: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    is_default: Optional[bool] = None


class CoverLetterResponse(BaseModel):
    id: int
    name: str
    body: str
    is_default: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
