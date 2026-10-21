from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Profile(BaseModel):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    other_links: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    custom_fields: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="profile")
