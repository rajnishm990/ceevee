from typing import AsyncGenerator 

from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker, async_session ,create_async_engine 

from app.core.config import settings 


engine = create_async_engine(
    settings.DATABASE_URL ,
    echo = settings.DEBUG ,
    future = True 
)

AsynSessionLocal = async_sessionmaker(
    bind = engine,
    class_ = AsyncSession ,
    expire_on_commit=False 

)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsynSessionLocal() as session:
        try:
            yield session 
            await session.commit 
        except Exception:
            await session.rollback()
            raise 

