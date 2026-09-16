"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    admin_role = sa.Enum("SUPER_ADMIN", "DISPATCHER", "OPERATOR", name="admin_role")
    application_type = sa.Enum("METER_NOT_WORKING", "MPI_REMOVAL", "GAS_LEAK", name="application_type")
    application_status = sa.Enum("NEW", "IN_PROGRESS", "COMPLETED", "REJECTED", name="application_status")
    application_priority = sa.Enum("NORMAL", "HIGH", "CRITICAL", name="application_priority")
    file_type = sa.Enum("METER_PHOTO", "GAS_LEAK_PHOTO", "OTHER", name="file_type")

    bind = op.get_bind()
    admin_role.create(bind, checkfirst=True)
    application_type.create(bind, checkfirst=True)
    application_status.create(bind, checkfirst=True)
    application_priority.create(bind, checkfirst=True)
    file_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_telegram_user_id", "users", ["telegram_user_id"], unique=True)

    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", admin_role, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_admins_email", "admins", ["email"], unique=True)

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_number", sa.String(32), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("personal_account", sa.String(64), nullable=False),
        sa.Column("application_type", application_type, nullable=False),
        sa.Column("status", application_status, nullable=False, server_default="NEW"),
        sa.Column("priority", application_priority, nullable=False, server_default="NORMAL"),
        sa.Column("requested_date", sa.Date(), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("assigned_to", sa.Integer(), sa.ForeignKey("admins.id"), nullable=True),
        sa.Column("admin_comment", sa.Text(), nullable=True),
    )
    op.create_index("ix_applications_application_number", "applications", ["application_number"], unique=True)
    op.create_index("ix_applications_personal_account", "applications", ["personal_account"])

    op.create_table(
        "application_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("file_type", file_type, nullable=False),
        sa.Column("telegram_file_id", sa.String(255), nullable=True),
        sa.Column("storage_url", sa.String(1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "application_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admins.id"), nullable=True),
        sa.Column("old_status", application_status, nullable=True),
        sa.Column("new_status", application_status, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admins.id"), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity", sa.String(128), nullable=True),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("system_settings")
    op.drop_table("application_history")
    op.drop_table("application_files")
    op.drop_table("applications")
    op.drop_table("admins")
    op.drop_table("users")

    bind = op.get_bind()
    sa.Enum(name="file_type").drop(bind, checkfirst=True)
    sa.Enum(name="application_priority").drop(bind, checkfirst=True)
    sa.Enum(name="application_status").drop(bind, checkfirst=True)
    sa.Enum(name="application_type").drop(bind, checkfirst=True)
    sa.Enum(name="admin_role").drop(bind, checkfirst=True)
