from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_any_admin
from app.database import get_db
from app.models.admin import Admin
from app.repositories.application_repo import ApplicationRepository
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_any_admin)):
    repo = ApplicationRepository(db)
    stats = await repo.stats()
    type_distribution = await repo.type_distribution()
    daily_counts = await repo.daily_counts()
    return DashboardStats(**stats, type_distribution=type_distribution, daily_counts=daily_counts)
