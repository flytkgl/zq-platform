"""adjust writeback value mode default

Revision ID: c6e7f8a9b0c1
Revises: a2c4f8e1b9d0
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c6e7f8a9b0c1"
down_revision: Union[str, None] = "a2c4f8e1b9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "form_writeback_rule",
        "value_mode",
        server_default="custom",
    )


def downgrade() -> None:
    op.alter_column(
        "form_writeback_rule",
        "value_mode",
        server_default="direct",
    )
