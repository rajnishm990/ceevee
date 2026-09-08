from datetime import datetime , timezone 

from sqlalchemy import DateTime 
from sqlalchemy.orm import DeclarativeBase , Mapped , declared_attr , mapped_column 



class BaseModel(DeclarativeBase):
    """ abstract base calss for all models , generates tables and standards like timestamps """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    # timezone aware timestamp 
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False 
    )
    updated_at: Mapped[DateTime]= mapped_column(
        DateTime(timezone=True),
        default= lambda : datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable= False 
    )