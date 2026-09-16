from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import FileType


class ApplicationFile(Base):
    __tablename__ = "application_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType, name="file_type"), nullable=False)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="files")
