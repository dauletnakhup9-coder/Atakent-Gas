from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application
from app.models.application_history import ApplicationHistory
from app.models.enums import ApplicationStatus, ApplicationType, Priority


class ApplicationFilters:
    def __init__(
        self,
        personal_account: str | None = None,
        application_number: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        application_type: ApplicationType | None = None,
        status: ApplicationStatus | None = None,
        priority: Priority | None = None,
        assigned_to: int | None = None,
        search: str | None = None,
    ) -> None:
        self.personal_account = personal_account
        self.application_number = application_number
        self.date_from = date_from
        self.date_to = date_to
        self.application_type = application_type
        self.status = status
        self.priority = priority
        self.assigned_to = assigned_to
        self.search = search


class ApplicationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _apply_filters(self, stmt: Select, f: ApplicationFilters) -> Select:
        if f.personal_account:
            stmt = stmt.where(Application.personal_account.ilike(f"%{f.personal_account}%"))
        if f.application_number:
            stmt = stmt.where(Application.application_number.ilike(f"%{f.application_number}%"))
        if f.date_from:
            stmt = stmt.where(func.date(Application.created_at) >= f.date_from)
        if f.date_to:
            stmt = stmt.where(func.date(Application.created_at) <= f.date_to)
        if f.application_type:
            stmt = stmt.where(Application.application_type == f.application_type)
        if f.status:
            stmt = stmt.where(Application.status == f.status)
        if f.priority:
            stmt = stmt.where(Application.priority == f.priority)
        if f.assigned_to:
            stmt = stmt.where(Application.assigned_to == f.assigned_to)
        if f.search:
            like = f"%{f.search}%"
            stmt = stmt.where(
                (Application.application_number.ilike(like)) | (Application.personal_account.ilike(like))
            )
        return stmt

    SORT_COLUMNS = {
        "created_at": Application.created_at,
        "application_number": Application.application_number,
        "priority": Application.priority,
        "status": Application.status,
    }

    async def list_paginated(
        self,
        filters: ApplicationFilters,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[list[Application], int]:
        base = select(Application)
        base = self._apply_filters(base, filters)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        column = self.SORT_COLUMNS.get(sort_by, Application.created_at)
        order = column.asc() if sort_dir == "asc" else column.desc()

        stmt = (
            base.options(selectinload(Application.user), selectinload(Application.assigned_admin))
            .order_by(order)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, application_id: int) -> Application | None:
        stmt = (
            select(Application)
            .where(Application.id == application_id)
            .options(
                selectinload(Application.user),
                selectinload(Application.assigned_admin),
                selectinload(Application.files),
                selectinload(Application.history).selectinload(ApplicationHistory.admin),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_number(self, application_number: str) -> Application | None:
        stmt = (
            select(Application)
            .where(Application.application_number == application_number)
            .options(selectinload(Application.files), selectinload(Application.history))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int, limit: int = 20) -> list[Application]:
        stmt = (
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def stats(self) -> dict:
        total = (await self.db.execute(select(func.count()).select_from(Application))).scalar_one()

        async def count_status(status: ApplicationStatus) -> int:
            stmt = select(func.count()).select_from(Application).where(Application.status == status)
            return (await self.db.execute(stmt)).scalar_one()

        critical_stmt = (
            select(func.count())
            .select_from(Application)
            .where(Application.priority == Priority.CRITICAL, Application.status != ApplicationStatus.COMPLETED)
        )
        critical = (await self.db.execute(critical_stmt)).scalar_one()

        return {
            "total": total,
            "new": await count_status(ApplicationStatus.NEW),
            "in_progress": await count_status(ApplicationStatus.IN_PROGRESS),
            "completed": await count_status(ApplicationStatus.COMPLETED),
            "rejected": await count_status(ApplicationStatus.REJECTED),
            "critical": critical,
        }

    async def type_distribution(self) -> dict[str, int]:
        stmt = select(Application.application_type, func.count()).group_by(Application.application_type)
        result = await self.db.execute(stmt)
        return {row[0].value: row[1] for row in result.all()}

    async def daily_counts(self, days: int = 14) -> list[dict]:
        stmt = (
            select(func.date(Application.created_at).label("day"), func.count())
            .group_by("day")
            .order_by("day")
        )
        result = await self.db.execute(stmt)
        return [{"date": str(row[0]), "count": row[1]} for row in result.all()]
