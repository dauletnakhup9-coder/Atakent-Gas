from pydantic import BaseModel, EmailStr

from app.models.enums import AdminRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: "AdminOut"


class AdminOut(BaseModel):
    id: int
    name: str
    email: str
    role: AdminRole
    active: bool

    model_config = {"from_attributes": True}


class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: AdminRole


TokenResponse.model_rebuild()
