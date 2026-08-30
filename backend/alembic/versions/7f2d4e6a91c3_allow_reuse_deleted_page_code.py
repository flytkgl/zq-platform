"""allow reusing page codes after soft delete

Revision ID: 7f2d4e6a91c3
Revises: 4cfc2f527944
Create Date: 2026-08-30

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7f2d4e6a91c3"
down_revision: Union[str, None] = "4cfc2f527944"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The initial schema created a table-level UNIQUE constraint on code.
    # Replace it with an active-row-only unique index so soft-deleted pages
    # do not block a new page with the same code.
    op.drop_constraint("page_meta_code_key", "page_meta", type_="unique")
    op.create_index(
        "ix_page_meta_code_active",
        "page_meta",
        ["code"],
        unique=True,
        postgresql_where="is_deleted = false",
    )


def downgrade() -> None:
    op.drop_index("ix_page_meta_code_active", table_name="page_meta")
    op.create_unique_constraint("page_meta_code_key", "page_meta", ["code"])
