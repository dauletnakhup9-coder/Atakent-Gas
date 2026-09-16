from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ApplicationStatus, ApplicationType, Priority


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    personal_account: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    application_type: Mapped[ApplicationType] = mapped_column(
        Enum(ApplicationType, name="application_type"), nullable=False
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.NEW,
        nullable=False,
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="application_priority"), default=Priority.NORMAL, nullable=False
    )
    requested_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("admins.id"), nullable=True)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="applications")
    assigned_admin: Mapped["Admin | None"] = relationship(
        back_populates="assigned_applications", foreign_keys=[assigned_to]
    )
    files: Mapped[list["ApplicationFile"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    history: Mapped[list["ApplicationHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationHistory.created_at"
    )
