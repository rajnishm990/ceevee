import pytest
from pydantic import ValidationError

from app.core.config import DEV_PDF_ENCRYPTION_KEY, DEV_SECRET_KEY, LocalSettings, ProductionSettings

GOOD = dict(
    SECRET_KEY="x" * 48,
    PDF_ENCRYPTION_KEY="MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=",
    DATABASE_URL="postgresql+asyncpg://u:p@db:5432/ceevee",
    RATE_LIMIT_STORAGE_URI="redis://redis:6379/0",
    ALLOWED_HOSTS=["api.example.com"],
    CORS_ORIGIN_REGEX=r"^https://app\.example\.com$",
)


def prod(**overrides):
    return ProductionSettings(_env_file=None, **{**GOOD, **overrides})


def test_local_settings_need_no_configuration():
    s = LocalSettings(_env_file=None)
    assert s.DATABASE_URL.startswith("sqlite") and s.STORAGE_BACKEND == "local" and s.AUTO_MIGRATE


def test_valid_production_settings_load():
    s = prod()
    assert s.STORAGE_BACKEND == "s3" and not s.AUTO_MIGRATE and not s.DEBUG


@pytest.mark.parametrize(
    "override",
    [
        {"SECRET_KEY": DEV_SECRET_KEY},
        {"SECRET_KEY": "short"},
        {"PDF_ENCRYPTION_KEY": DEV_PDF_ENCRYPTION_KEY},
        {"ALLOWED_HOSTS": ["*"]},
        {"DATABASE_URL": "sqlite+aiosqlite:///./x.db"},
        {"RATE_LIMIT_STORAGE_URI": "memory://"},
        {"DEBUG": True},
    ],
)
def test_unsafe_production_config_is_rejected(override):
    with pytest.raises(ValidationError):
        prod(**override)


@pytest.mark.parametrize("missing", ["SECRET_KEY", "PDF_ENCRYPTION_KEY", "DATABASE_URL", "ALLOWED_HOSTS", "CORS_ORIGIN_REGEX"])
def test_production_requires_explicit_values(missing, monkeypatch):
    values = {k: v for k, v in GOOD.items() if k != missing}
    with pytest.raises(ValidationError):
        ProductionSettings(_env_file=None, **values)


def test_invalid_encryption_key_length_rejected():
    with pytest.raises(ValidationError):
        prod(PDF_ENCRYPTION_KEY="c2hvcnQ=")
