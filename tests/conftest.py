from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import BaseModel
from app.db.session import get_db
from app.main import app


@pytest.fixture(autouse=True)
def isolated_storage_dir(tmp_path: Path, monkeypatch):
    """Point encrypted PDF storage at a throwaway temp dir per test instead
    of the real local_storage/ folder, so running the suite doesn't leave
    files behind in the project."""
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(tmp_path / "local_storage"))


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Each test gets a fresh in-memory SQLite DB - fast, isolated, no
    leftover state between tests, no need to touch the real ceevee_local.db."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with session_factory() as session:
            yield session
            await session.commit()

    app.dependency_overrides[get_db] = _override_get_db

    async with session_factory() as session:
        yield session

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture()
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
