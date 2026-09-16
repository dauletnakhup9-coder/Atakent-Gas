from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_any_admin, require_super_admin
from app.database import get_db
from app.models.admin import Admin
from app.schemas.dashboard import SettingsUpdate
from app.services.settings_service import SUPER_ADMIN_ONLY_KEYS, get_all_settings, update_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def read_settings(db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_any_admin)):
    return await get_all_settings(db)


@router.patch("")
async def write_settings(
    payload: SettingsUpdate, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_any_admin)
):
    values = payload.values
    if admin.role.value != "SUPER_ADMIN":
        values = {k: v for k, v in values.items() if k not in SUPER_ADMIN_ONLY_KEYS}
    return await update_settings(db, values)
