from typing import List , Dict , Any , Optional , TYPE_CHECKING
from sqlalchemy import String , Boolean , JSON 
from sqlalchemy.orm import mapped_column , Mapped , relationship 
from app.db.base import BaseModel

if TYPE_CHECKING:
    from app.models.cover_letter import CoverLetterTemplate 
    from app.models.profile import Profile 
    from app.models.section import ResumeSection 

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

    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    cover_letters: Mapped[List["CoverLetterTemplate"]] = relationship(
        "CoverLetterTemplate", back_populates="user", cascade="all, delete-orphan"
    )
