from typing import Optional 
from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 

from app.models.user import User 
from app.schemas.user import UserCreate 

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session 

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user_in: UserCreate, hashed_password: str) -> User:
        db_obj = User(email=user_in.email , hashed_password= hashed_password)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return  db_obj