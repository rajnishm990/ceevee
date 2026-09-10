from fastapi import Depends 
from fastapi.security import OAuth2PasswordBearer 
from sqlalchemy.ext.asyncio import AsyncSession 
from app.core.exceptions import InvalidCredentialsException 
from app.core.security import decode_token 
from app.models.user import User  
from app.db.session import get_db 
from app.repositories.user_repo import UserRepository 
from app.repositories.section_repo import SectionRepository 
from app.repositories.version_repo import VersionRepository 
from app.services.resume_service import ResumeService 


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")  #token url is only for populating OpenAPi docs , login itself takes Json , not a form 


async def get_current_user(token: str = Depends(oauth2_scheme), db:AsyncSession = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise InvalidCredentialsException("Invalid or expired token") from exc 

    if payload.get["type"] != "access":
        raise InvalidCredentialsException("This is not an access token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(payload["sub"]))
    if not user or not user.is_active:
        raise InvalidCredentialsException()
    return user 

def get_user_repo(db:AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_resume_service(db: AsyncSession = Depends(get_db)) -> ResumeService:
    return ResumeService(SectionRepository(db), VersionRepository(db))
