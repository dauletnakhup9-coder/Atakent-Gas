from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.security import verify_password
from app.models.admin import Admin
from app.repositories.admin_repo import AdminRepository


async def authenticate_admin(db: AsyncSession, email: str, password: str) -> tuple[Admin, str]:
    repo = AdminRepository(db)
    admin = await repo.get_by_email(email.lower())
    if admin is None or not admin.active or not verify_password(password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email немесе құпия сөз қате")

    token = create_access_token(subject=str(admin.id), role=admin.role.value)
    return admin, token
