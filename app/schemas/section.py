from typing import List , Optional 
from pydantic import BaseModel , ConfigDict , Field 
from app.schemas.version import VersionSummary 


class SectionCreate(BaseModel):
    domain_name : str = Field(min_length=1 , max_length=50)
    grive_link: Optional[str] = None 

class SectionUpdate(BaseModel):
    domain_name: Optional[str] = Field(default=None , min_length=1 , max_length=50)
    grive_link: Optional[str] = None  

class SetActiveVersionRequest(BaseModel):
    version_id: int 

class SectionResponse(BaseModel):
    id: int 
    domain_name: str 
    shareable_slug : str 
    grive_link : Optional[str]
    active_version_id: Optional[int]

    model_config= ConfigDict(from_attributes=True)

class SectionWithVersions(SectionResponse):
    versions : List[VersionSummary] = []