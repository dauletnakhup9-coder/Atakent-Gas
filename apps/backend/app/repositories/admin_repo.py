from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin


class AdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, admin_id: int) -> Admin | None:
        return await self.db.get(Admin, admin_id)

    async def get_by_email(self, email: str) -> Admin | None:
        result = await self.db.execute(select(Admin).where(Admin.email == email.lower()))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Admin]:
        result = await self.db.execute(select(Admin).order_by(Admin.created_at.desc()))
        return list(result.scalars().all())

    async def create(self, admin: Admin) -> Admin:
        self.db.add(admin)
        await self.db.commit()
        await self.db.refresh(admin)
        return admin
