from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_dispatcher_or_above, require_super_admin
from app.auth.security import hash_password
from app.database import get_db
from app.models.admin import Admin
from app.repositories.admin_repo import AdminRepository
from app.schemas.auth import AdminCreate, AdminOut

router = APIRouter(prefix="/admins", tags=["admins"])


@router.get("", response_model=list[AdminOut])
async def list_admins(db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_dispatcher_or_above)):
    repo = AdminRepository(db)
    return await repo.list_all()


@router.post("", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: AdminCreate, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_super_admin)
):
    repo = AdminRepository(db)
    existing = await repo.get_by_email(payload.email.lower())
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email тіркелген")

    new_admin = Admin(
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=True,
    )
    return await repo.create(new_admin)
