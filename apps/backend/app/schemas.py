import re
import string
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.config import get_settings
from app.models import (
    AlertStatus,
    ApplicationType,
    Priority,
    Role,
    SecuritySeverity,
    Status,
)


def verify_personal_account(account_number: str) -> dict:
    """Adapter boundary: replace with subscriber API. Format is NOT existence verification."""
    if not re.fullmatch(r"[0-9]{6,20}", account_number):
        raise ValueError("Дербес шот 6–20 цифрдан тұруы керек")

    return {
        "format_valid": True,
        "subscriber_verified": False,
    }


def local_today() -> date:
    return datetime.now(
        ZoneInfo(get_settings().timezone)
    ).date()


# =========================================================
# BASE
# =========================================================

class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


# =========================================================
# TELEGRAM USER
# =========================================================

class TelegramUser(StrictModel):
    telegram_user_id: int = Field(
        gt=0,
        le=2**52,
    )

    telegram_username: str | None = Field(
        None,
        max_length=64,
        pattern=r"^[A-Za-z0-9_]+$",
    )

    first_name: str = Field(
        min_length=1,
        max_length=256,
    )

    last_name: str | None = Field(
        None,
        max_length=256,
    )


# =========================================================
# APPLICATION CREATE
# =========================================================

class CreateApplication(StrictModel):
    user: TelegramUser

    idempotency_key: UUID

    personal_account: str

    application_type: ApplicationType

    requested_date: date | None = None

    latitude: float | None = Field(
        None,
        ge=-90,
        le=90,
        allow_inf_nan=False,
    )

    longitude: float | None = Field(
        None,
        ge=-180,
        le=180,
        allow_inf_nan=False,
    )

    meter_photo_id: UUID | None = None

    leak_photo_id: UUID | None = None

    @field_validator("personal_account")
    @classmethod
    def account(cls, value):
        verify_personal_account(value)
        return value

    @model_validator(mode="after")
    def required_fields(self):
        if self.application_type == ApplicationType.MPI_REMOVAL:

            if (
                self.requested_date is None
                or not local_today()
                <= self.requested_date
                <= date(
                    local_today().year + 2,
                    12,
                    31,
                )
            ):
                raise ValueError(
                    "МПИ күні бүгіннен бастап екі жыл шегінде болуы керек"
                )

            if any(
                x is not None
                for x in [
                    self.meter_photo_id,
                    self.leak_photo_id,
                    self.latitude,
                    self.longitude,
                ]
            ):
                raise ValueError(
                    "МПИ өтініміне фото/геолокация қажет емес"
                )

        else:

            if (
                self.meter_photo_id is None
                or self.latitude is None
                or self.longitude is None
            ):
                raise ValueError(
                    "Фото және геолокация міндетті"
                )

            if self.requested_date is not None:
                raise ValueError(
                    "Бұл өтінімге МПИ күні қажет емес"
                )

            if self.application_type == ApplicationType.GAS_LEAK:

                if (
                    self.leak_photo_id is None
                    or self.leak_photo_id
                    == self.meter_photo_id
                ):
                    raise ValueError(
                        "Екі бөлек фото міндетті"
                    )

            elif self.leak_photo_id is not None:
                raise ValueError(
                    "Артық фото"
                )

        return self


# =========================================================
# AUTH
# =========================================================

class Login(StrictModel):
    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )


class CreateAdmin(StrictModel):
    name: str = Field(
        min_length=2,
        max_length=200,
    )

    email: EmailStr

    password: str = Field(
        min_length=12,
        max_length=128,
    )

    role: Role


class UpdateAdmin(StrictModel):
    active: bool


# =========================================================
# VERSIONING
# =========================================================

class Versioned(StrictModel):
    version: int = Field(
        ge=1,
    )


# =========================================================
# APPLICATION UPDATE
# =========================================================

class StatusUpdate(Versioned):
    status: Status

    comment: str | None = Field(
        None,
        max_length=2000,
    )

    public_comment: bool = False


class Assignment(Versioned):
    assigned_to: int | None = Field(
        None,
        gt=0,
    )


class ApplicationUpdate(Versioned):
    priority: Priority | None = None

    admin_comment: str | None = Field(
        None,
        max_length=2000,
    )


class Comment(Versioned):
    comment: str = Field(
        min_length=1,
        max_length=2000,
    )

    public_comment: bool = False


# =========================================================
# SETTINGS
# =========================================================

class SettingsUpdate(StrictModel):
    organization_name: str = Field(
        min_length=1,
        max_length=200,
    )

    contact_phone: str = Field(
        max_length=40,
        pattern=r"^[+0-9 ()-]*$",
    )

    emergency_phone: str = Field(
        max_length=40,
        pattern=r"^[+0-9 ()-]*$",
    )

    max_photo_mb: int = Field(
        ge=1,
        le=10,
    )

    notification_texts: dict[str, str]

    @field_validator("notification_texts")
    @classmethod
    def templates(cls, value):

        if set(value) != {
            "IN_PROGRESS",
            "COMPLETED",
            "REJECTED",
        }:
            raise ValueError(
                "Үш мәртебе мәтіні қажет"
            )

        for template in value.values():

            if not 1 <= len(template) <= 1000:
                raise ValueError(
                    "Мәтін 1–1000 таңба болуы керек"
                )

            for (
                _,
                field,
                spec,
                conversion,
            ) in string.Formatter().parse(template):

                if field is not None and (
                    field != "number"
                    or spec
                    or conversion
                ):
                    raise ValueError(
                        "Тек {number} өрісіне рұқсат етіледі"
                    )

        return value


# =========================================================
# SECURITY EVENT SCHEMAS
# =========================================================

class SecurityEventCreate(StrictModel):
    source: str = Field(
        min_length=1,
        max_length=30,
    )

    severity: SecuritySeverity = SecuritySeverity.INFO

    signature: str | None = Field(
        None,
        max_length=500,
    )

    src_ip: str | None = Field(
        None,
        max_length=45,
    )

    src_country: str | None = Field(
        None,
        max_length=100,
    )

    dst_port: int | None = Field(
        None,
        ge=1,
        le=65535,
    )

    action: str | None = Field(
        None,
        max_length=50,
    )

    raw: dict | None = None


class SecurityEventResponse(StrictModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: int
    source: str
    severity: SecuritySeverity
    signature: str | None
    src_ip: str | None
    src_country: str | None
    dst_port: int | None
    action: str | None
    raw: dict | None
    created_at: datetime


# =========================================================
# BLOCKED IP SCHEMAS
# =========================================================

class BlockIPCreate(StrictModel):
    ip: str = Field(
        min_length=3,
        max_length=45,
    )

    reason: str | None = Field(
        None,
        max_length=500,
    )

    expires_at: datetime | None = None


class BlockedIPResponse(StrictModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: int
    ip: str
    reason: str | None
    source: str
    blocked_by: int | None
    expires_at: datetime | None
    created_at: datetime


# =========================================================
# ALERT SCHEMAS
# =========================================================

class AlertCreate(StrictModel):
    type: str = Field(
        min_length=1,
        max_length=100,
    )

    severity: SecuritySeverity = SecuritySeverity.WARNING

    message: str = Field(
        min_length=1,
        max_length=5000,
    )


class AlertUpdate(StrictModel):
    status: AlertStatus


class AlertResponse(StrictModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    id: int
    type: str
    severity: SecuritySeverity
    message: str
    status: AlertStatus
    acknowledged_by: int | None
    created_at: datetime
    resolved_at: datetime | None
    # =========================================================
# API KEYS
# =========================================================

class ApiKeyCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
    )

    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_by: int | None
    active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ApiKeyCreatedResponse(ApiKeyResponse):
    key: str