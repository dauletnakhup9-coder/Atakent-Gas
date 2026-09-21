"""add security tables"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f7d40bfc5f71"
branch_labels = None
depends_on = None


def upgrade():
    # =====================================================
    # SECURITY EVENTS
    # =====================================================

    op.create_table(
        "security_events",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "INFO",
                "WARNING",
                "HIGH",
                "CRITICAL",
                name="security_severity",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "signature",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "src_ip",
            sa.String(length=45),
            nullable=True,
        ),
        sa.Column(
            "src_country",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "dst_port",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "raw",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_security_events"),
        ),
    )

    op.create_index(
        op.f("ix_security_events_source"),
        "security_events",
        ["source"],
        unique=False,
    )

    op.create_index(
        op.f("ix_security_events_severity"),
        "security_events",
        ["severity"],
        unique=False,
    )

    op.create_index(
        op.f("ix_security_events_src_ip"),
        "security_events",
        ["src_ip"],
        unique=False,
    )

    op.create_index(
        op.f("ix_security_events_created_at"),
        "security_events",
        ["created_at"],
        unique=False,
    )

    # =====================================================
    # BLOCKED IPS
    # =====================================================

    op.create_table(
        "blocked_ips",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "ip",
            sa.String(length=45),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "blocked_by",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["blocked_by"],
            ["admins.id"],
            name=op.f(
                "fk_blocked_ips_blocked_by_admins"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_blocked_ips"),
        ),
        sa.UniqueConstraint(
            "ip",
            name=op.f("uq_blocked_ips_ip"),
        ),
    )

    op.create_index(
        op.f("ix_blocked_ips_ip"),
        "blocked_ips",
        ["ip"],
        unique=False,
    )

    op.create_index(
        op.f("ix_blocked_ips_blocked_by"),
        "blocked_ips",
        ["blocked_by"],
        unique=False,
    )

    op.create_index(
        op.f("ix_blocked_ips_created_at"),
        "blocked_ips",
        ["created_at"],
        unique=False,
    )

    # =====================================================
    # ALERTS
    # =====================================================

    op.create_table(
        "alerts",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "INFO",
                "WARNING",
                "HIGH",
                "CRITICAL",
                name="alert_severity",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "ACK",
                "RESOLVED",
                name="alert_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "acknowledged_by",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["acknowledged_by"],
            ["admins.id"],
            name=op.f(
                "fk_alerts_acknowledged_by_admins"
            ),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_alerts"),
        ),
    )

    op.create_index(
        op.f("ix_alerts_type"),
        "alerts",
        ["type"],
        unique=False,
    )

    op.create_index(
        op.f("ix_alerts_severity"),
        "alerts",
        ["severity"],
        unique=False,
    )

    op.create_index(
        op.f("ix_alerts_status"),
        "alerts",
        ["status"],
        unique=False,
    )

    op.create_index(
        op.f("ix_alerts_created_at"),
        "alerts",
        ["created_at"],
        unique=False,
    )


def downgrade():
    # =====================================================
    # ALERTS
    # =====================================================

    op.drop_index(
        op.f("ix_alerts_created_at"),
        table_name="alerts",
    )

    op.drop_index(
        op.f("ix_alerts_status"),
        table_name="alerts",
    )

    op.drop_index(
        op.f("ix_alerts_severity"),
        table_name="alerts",
    )

    op.drop_index(
        op.f("ix_alerts_type"),
        table_name="alerts",
    )

    op.drop_table("alerts")

    # =====================================================
    # BLOCKED IPS
    # =====================================================

    op.drop_index(
        op.f("ix_blocked_ips_created_at"),
        table_name="blocked_ips",
    )

    op.drop_index(
        op.f("ix_blocked_ips_blocked_by"),
        table_name="blocked_ips",
    )

    op.drop_index(
        op.f("ix_blocked_ips_ip"),
        table_name="blocked_ips",
    )

    op.drop_table("blocked_ips")

    # =====================================================
    # SECURITY EVENTS
    # =====================================================

    op.drop_index(
        op.f("ix_security_events_created_at"),
        table_name="security_events",
    )

    op.drop_index(
        op.f("ix_security_events_src_ip"),
        table_name="security_events",
    )

    op.drop_index(
        op.f("ix_security_events_severity"),
        table_name="security_events",
    )

    op.drop_index(
        op.f("ix_security_events_source"),
        table_name="security_events",
    )

    op.drop_table("security_events")