import asyncio 

from app.core.exceptions import ForbiddenException 
from app.core.security import verify_password 
from app.models.user import User 
from app.repositories.section_repo import SectionRepository 
from app.repositories.user_repo import UserRepository 
from app.services.resume_service import ResumeService 
from app.services.storage_service import StorageService 


class AccountService:
    def __init__(self , user_repo: UserRepository, section_repo: SectionRepository):
        self.user_repo = user_repo
        self.section_repo = section_repo 

    async def delete_account(self, user: User , password: str) -> None:
        if not await asyncio.to_thread(verify_password, password, user.hashed_password):
            raise ForbiddenException("Incorrect Password")
        sections = await self.section_repo.list_for_user(user.id)
        paths = ResumeService._paths_of([v for s in sections for v in s.versions])
        await self.user_repo.delete(user)
        for path in paths:
            await StorageService.delete_file(path)