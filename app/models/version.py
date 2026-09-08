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