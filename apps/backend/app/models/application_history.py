from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ApplicationStatus


class ApplicationHistory(Base):
    __tablename__ = "application_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admins.id"), nullable=True)
    old_status: Mapped[ApplicationStatus | None] = mapped_column(
        Enum(ApplicationStatus, name="application_status"), nullable=True
    )
    new_status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="history")
    admin: Mapped["Admin | None"] = relationship()
