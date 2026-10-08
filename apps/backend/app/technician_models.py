"""Field technicians who install meter seals, independent of the resident/subscriber registry."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utcnow


class Technician(Base):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(default=1)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("admins.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SealInstallation(Base):
    __tablename__ = "seal_installations"
    __table_args__ = (
        UniqueConstraint("telegram_user_id", "idempotency_key"),
        CheckConstraint("reading_value >= 0", name="nonnegative_reading"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="seal_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="seal_longitude"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"), index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger)
    idempotency_key: Mapped[str] = mapped_column(String(36))
    account_number: Mapped[str] = mapped_column(String(20), index=True)
    meter_number: Mapped[str] = mapped_column(String(40))
    reading_value: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    seal_number: Mapped[str] = mapped_column(String(40))
    photo_id: Mapped[str] = mapped_column(ForeignKey("application_files.id"))
    latitude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
