"""Field technicians and their seal-installation reports.

Adds the technicians table (staff registered by a SUPER_ADMIN, not residents),
the seal_installations table they submit from the bot, and SEAL_PHOTO to the
file-type check constraint. SEAL_PHOTO (10 chars) fits the column's existing
VARCHAR(19), sized for METER_READING_PHOTO, so no column width change is needed.
"""
from alembic import op
import sqlalchemy as sa

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(op.f("ck_application_files_filetype"), "application_files", type_="check")
    op.create_check_constraint(
        op.f("ck_application_files_filetype"),
        "application_files",
        "file_type IN ('METER_PHOTO', 'GAS_LEAK_PHOTO', 'METER_READING_PHOTO', 'SEAL_PHOTO', 'OTHER')",
    )
    op.create_table(
        "technicians",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["admins.id"], name=op.f("fk_technicians_created_by_admins")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_technicians")),
        sa.UniqueConstraint("telegram_user_id", name=op.f("uq_technicians_telegram_user_id")),
    )
    op.create_table(
        "seal_installations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("technician_id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("idempotency_key", sa.String(36), nullable=False),
        sa.Column("account_number", sa.String(20), nullable=False),
        sa.Column("meter_number", sa.String(40), nullable=False),
        sa.Column("reading_value", sa.Numeric(14, 3), nullable=False),
        sa.Column("seal_number", sa.String(40), nullable=False),
        sa.Column("photo_id", sa.String(36), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("reading_value >= 0", name=op.f("ck_seal_installations_nonnegative_reading")),
        sa.CheckConstraint("latitude BETWEEN -90 AND 90", name=op.f("ck_seal_installations_seal_latitude")),
        sa.CheckConstraint("longitude BETWEEN -180 AND 180", name=op.f("ck_seal_installations_seal_longitude")),
        sa.ForeignKeyConstraint(["technician_id"], ["technicians.id"], name=op.f("fk_seal_installations_technician_id_technicians")),
        sa.ForeignKeyConstraint(["photo_id"], ["application_files.id"], name=op.f("fk_seal_installations_photo_id_application_files")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_seal_installations")),
        sa.UniqueConstraint("telegram_user_id", "idempotency_key", name=op.f("uq_seal_installations_telegram_user_id")),
    )
    op.create_index(op.f("ix_seal_installations_technician_id"), "seal_installations", ["technician_id"])
    op.create_index(op.f("ix_seal_installations_account_number"), "seal_installations", ["account_number"])


def downgrade():
    op.drop_index(op.f("ix_seal_installations_account_number"), table_name="seal_installations")
    op.drop_index(op.f("ix_seal_installations_technician_id"), table_name="seal_installations")
    op.drop_table("seal_installations")
    op.drop_table("technicians")
    op.drop_constraint(op.f("ck_application_files_filetype"), "application_files", type_="check")
    op.create_check_constraint(
        op.f("ck_application_files_filetype"),
        "application_files",
        "file_type IN ('METER_PHOTO', 'GAS_LEAK_PHOTO', 'METER_READING_PHOTO', 'OTHER')",
    )
