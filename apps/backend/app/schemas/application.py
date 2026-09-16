from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ApplicationStatus, ApplicationType, FileType, Priority


class BotFileInput(BaseModel):
    file_type: FileType
    telegram_file_id: str


class BotUserInput(BaseModel):
    telegram_user_id: int
    telegram_username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class BotCreateApplicationRequest(BaseModel):
    user: BotUserInput
    personal_account: str = Field(min_length=4, max_length=64)
    application_type: ApplicationType
    requested_date: date | None = None
    latitude: float | None = None
    longitude: float | None = None
    files: list[BotFileInput] = Field(default_factory=list)

    @field_validator("personal_account")
    @classmethod
    def validate_account_format(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Дербес шот тек цифрлардан тұруы керек")
        return v


class UserOut(BaseModel):
    id: int
    telegram_user_id: int
    telegram_username: str | None
    first_name: str | None
    last_name: str | None

    model_config = {"from_attributes": True}


class ApplicationFileOut(BaseModel):
    id: int
    file_type: FileType
    storage_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationHistoryOut(BaseModel):
    id: int
    old_status: ApplicationStatus | None
    new_status: ApplicationStatus
    comment: str | None
    admin_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignedAdminOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class ApplicationOut(BaseModel):
    id: int
    application_number: str
    personal_account: str
    application_type: ApplicationType
    status: ApplicationStatus
    priority: Priority
    requested_date: date | None
    latitude: float | None
    longitude: float | None
    admin_comment: str | None
    created_at: datetime
    updated_at: datetime
    user: UserOut
    assigned_admin: AssignedAdminOut | None

    model_config = {"from_attributes": True}


class ApplicationDetailOut(ApplicationOut):
    files: list[ApplicationFileOut]
    history: list[ApplicationHistoryOut]


class ApplicationListOut(BaseModel):
    items: list[ApplicationOut]
    total: int
    page: int
    page_size: int


class StatusUpdateRequest(BaseModel):
    status: ApplicationStatus
    comment: str | None = None


class AssignRequest(BaseModel):
    admin_id: int


class CommentRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)
