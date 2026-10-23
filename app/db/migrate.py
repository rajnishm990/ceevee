from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[2]


def alembic_config(url: Optional[str] = None) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.attributes["configure_logger"] = False
    if url:
        cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return cfg


def upgrade_to_head(url: Optional[str] = None) -> None:
    command.upgrade(alembic_config(url), "head")


def check_no_drift(url: Optional[str] = None) -> None:
    command.check(alembic_config(url))
