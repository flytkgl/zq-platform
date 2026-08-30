"""add form writeback rules

Revision ID: a2c4f8e1b9d0
Revises: 7f2d4e6a91c3
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a2c4f8e1b9d0"
down_revision: Union[str, None] = "7f2d4e6a91c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "form_writeback_rule",
        sa.Column("source_form_id", sa.String(length=21), nullable=False),
        sa.Column("target_form_id", sa.String(length=21), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_name_auto", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_table_key", sa.String(length=100), nullable=False),
        sa.Column("target_table_key", sa.String(length=100), nullable=False),
        sa.Column("target_field", sa.String(length=100), nullable=False),
        sa.Column("trigger_events", sa.JSON(), nullable=False),
        sa.Column("value_mode", sa.String(length=20), nullable=False, server_default="direct"),
        sa.Column("source_value_field", sa.String(length=100), nullable=True),
        sa.Column("custom_expression", sa.Text(), nullable=True),
        sa.Column("writeback_operator", sa.String(length=20), nullable=False, server_default="set"),
        sa.Column("execute_conditions", sa.JSON(), nullable=True),
        sa.Column("value_filter_conditions", sa.JSON(), nullable=True),
        sa.Column("match_conditions", sa.JSON(), nullable=False),
        sa.Column("missing_target_policy", sa.String(length=20), nullable=False, server_default="error"),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=21), nullable=False),
        sa.Column("sort", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.Column("sys_create_datetime", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("sys_update_datetime", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("sys_creator_id", sa.String(length=21), nullable=True),
        sa.Column("sys_modifier_id", sa.String(length=21), nullable=True),
        sa.Column("sys_dept_id", sa.String(length=21), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_form_writeback_rule_source_form_id", "form_writeback_rule", ["source_form_id"])
    op.create_index("ix_form_writeback_rule_target_form_id", "form_writeback_rule", ["target_form_id"])
    op.create_index("ix_form_writeback_rule_enabled", "form_writeback_rule", ["enabled"])
    op.create_index("ix_form_writeback_rule_is_deleted", "form_writeback_rule", ["is_deleted"])
    op.create_index("idx_form_writeback_source_enabled", "form_writeback_rule", ["source_form_id", "enabled"])


def downgrade() -> None:
    op.drop_index("idx_form_writeback_source_enabled", table_name="form_writeback_rule")
    op.drop_index("ix_form_writeback_rule_is_deleted", table_name="form_writeback_rule")
    op.drop_index("ix_form_writeback_rule_enabled", table_name="form_writeback_rule")
    op.drop_index("ix_form_writeback_rule_target_form_id", table_name="form_writeback_rule")
    op.drop_index("ix_form_writeback_rule_source_form_id", table_name="form_writeback_rule")
    op.drop_table("form_writeback_rule")
