import asyncio
import os

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.db.migrate import alembic_config, check_no_drift, upgrade_to_head

URLS = ["sqlite+aiosqlite:///{tmp}/mig.db"]
PG = os.getenv("TEST_DATABASE_URL", "")
if PG.startswith("postgresql"):
    URLS.append(PG)


async def _reset_postgres(url: str) -> None:
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


@pytest.fixture(params=URLS, ids=lambda u: u.split(":")[0])
def migration_url(request, tmp_path):
    url = request.param.format(tmp=tmp_path)
    if url.startswith("postgresql"):
        asyncio.run(_reset_postgres(url))
    return url


def test_migrations_upgrade_cleanly(migration_url):
    upgrade_to_head(migration_url)


def test_models_and_migrations_have_not_drifted(migration_url):
    upgrade_to_head(migration_url)
    check_no_drift(migration_url)


def test_migrations_are_reversible(migration_url):
    upgrade_to_head(migration_url)
    command.downgrade(alembic_config(migration_url), "base")
    upgrade_to_head(migration_url)
