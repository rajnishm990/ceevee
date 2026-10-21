from typing import Optional 

from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 

from app.models.profile import Profile 
from app.schemas.profile import ProfileData 


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session 

    async def get_for_user(self, user_id: int) -> Optional[Profile]:
        result = await self.session.execute(select(Profile).where(Profile.user_id == user_id))
        return result.scalar_one_or_none()

    async def upsert(self , user_id: int , data: ProfileData) -> Profile:
        profile = await self.get_for_user(user_id)
        values = data.model_dump(mode="json")

        if profile is None:
            profile = Profile(user_id=user_id, **values) 
        else:
            for key , value in values.items():
                setattr(profile, key , value)
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile 

    