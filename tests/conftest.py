import os
from pathlib import Path
from typing import AsyncGenerator, Awaitable, Callable, Dict, List

import fitz
import pytest
from argon2 import PasswordHasher
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.base import BaseModel
from app.db.session import enable_sqlite_fk, get_db
from app.main import app


@pytest.fixture(autouse=True, scope="session")
def fast_password_hashing():
    import app.core.security as security

    original = security.pwd_hasher
    security.pwd_hasher = PasswordHasher(time_cost=1, memory_cost=1024, parallelism=1)
    yield
    security.pwd_hasher = original


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture(autouse=True)
def isolated_storage_dir(tmp_path: Path, monkeypatch) -> Path:
    storage = tmp_path / "local_storage"
    monkeypatch.setattr(settings, "LOCAL_STORAGE_DIR", str(storage))
    return storage


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    in_memory = TEST_DATABASE_URL.endswith(":memory:")
    engine = create_async_engine(TEST_DATABASE_URL, future=True, poolclass=None if in_memory else NullPool)
    enable_sqlite_fk(engine)
    async with engine.begin() as conn:
        if not in_memory:
            await conn.run_sync(BaseModel.metadata.drop_all)
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def make_pdf() -> Callable[..., bytes]:
    def _make(lines: List[str] = ("Junior Backend Engineer",), fontsize: float = 14) -> bytes:
        doc = fitz.open()
        page = doc.new_page()
        for i, text in enumerate(lines):
            page.insert_text((72, 100 + i * 30), text, fontsize=fontsize)
        data = doc.tobytes()
        doc.close()
        return data

    return _make


@pytest_asyncio.fixture()
async def register_user(client) -> Callable[[str], Awaitable[Dict[str, str]]]:
    async def _register(email: str = "user@example.com") -> Dict[str, str]:
        await client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret123"})
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _register


@pytest_asyncio.fixture()
async def headers(register_user) -> Dict[str, str]:
    return await register_user("owner@example.com")


@pytest_asyncio.fixture()
async def section(client, headers) -> dict:
    resp = await client.post("/api/v1/sections", json={"domain_name": "backend"}, headers=headers)
    return resp.json()


@pytest_asyncio.fixture()
async def upload(client, headers, make_pdf) -> Callable[..., Awaitable[dict]]:
    async def _upload(section_id: int, lines=("Junior Backend Engineer",), hdrs=None) -> dict:
        files = {"file": ("resume.pdf", make_pdf(list(lines)), "application/pdf")}
        resp = await client.post(f"/api/v1/sections/{section_id}/versions", files=files, headers=hdrs or headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _upload
