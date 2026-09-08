from pydantic import BaseModel , ConfigDict 
from typing import Dict , Any , Optional 
from datetime import datetime 


class ResumeVersionBase(BaseModel):
    content: Dict[str,str]

class ResumeVersionCreate(ResumeVersionBase):
    section_id = int 
    coordinate_map = Dict[str,Any]

class ResumeVersionResponse(ResumeVersionBase):
    id:int 
    section_id = int 
    created_at = datetime 

    #reads from sqlAlchemy directly
    model_config = ConfigDict(from_attributes=True)

class ResumeEditRequest(BaseModel):
    updated_content: Dict[str, str]

