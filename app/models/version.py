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
