from typing import Any , Dict 

from pydantic import BaseModel , ConfigDict , EmailStr , Field 


class UserCreate(BaseModel):
    email: EmailStr 
    password: str = Field(min_length=8 , max_length=128)

class UserLogin(BaseModel):
    email: EmailStr 
    password: str 

class UserResponse(BaseModel):
    id: int 
    email: EmailStr
    is_active = bool 
    base_profile: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class TokenPair(BaseModel):
    access_token : str 
    refresh_token : str 
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str 