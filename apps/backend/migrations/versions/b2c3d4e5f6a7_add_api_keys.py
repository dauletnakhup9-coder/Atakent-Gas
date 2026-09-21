"""add api keys

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-19
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "key_prefix",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "key_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["admins.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )

    op.create_index(
        "ix_api_keys_key_prefix",
        "api_keys",
        ["key_prefix"],
        unique=False,
    )

    op.create_index(
        "ix_api_keys_key_hash",
        "api_keys",
        ["key_hash"],
        unique=True,
    )

    op.create_index(
        "ix_api_keys_created_by",
        "api_keys",
        ["created_by"],
        unique=False,
    )

    op.create_index(
        "ix_api_keys_active",
        "api_keys",
        ["active"],
        unique=False,
    )

    op.create_index(
        "ix_api_keys_expires_at",
        "api_keys",
        ["expires_at"],
        unique=False,
    )

    op.create_index(
        "ix_api_keys_created_at",
        "api_keys",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_api_keys_created_at",
        table_name="api_keys",
    )

    op.drop_index(
        "ix_api_keys_expires_at",
        table_name="api_keys",
    )

    op.drop_index(
        "ix_api_keys_active",
        table_name="api_keys",
    )

    op.drop_index(
        "ix_api_keys_created_by",
        table_name="api_keys",
    )

    op.drop_index(
        "ix_api_keys_key_hash",
        table_name="api_keys",
    )

    op.drop_index(
        "ix_api_keys_key_prefix",
        table_name="api_keys",
    )

    op.drop_table("api_keys")