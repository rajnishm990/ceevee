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