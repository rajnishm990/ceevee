"""version revision counter

Revision ID: 0002
Revises: 67153501288d
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "67153501288d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("resume_versions", sa.Column("revision", sa.Integer(), server_default="1", nullable=False))


def downgrade() -> None:
    op.drop_column("resume_versions", "revision")
