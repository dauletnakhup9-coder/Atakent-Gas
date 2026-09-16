import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import require_any_admin
from app.database import get_db
from app.models.admin import Admin
from app.models.enums import ApplicationStatus, ApplicationType
from app.repositories.application_repo import ApplicationFilters, ApplicationRepository

router = APIRouter(prefix="/reports", tags=["reports"])


async def _build_report(
    db: AsyncSession,
    date_from: date | None,
    date_to: date | None,
    application_type: ApplicationType | None,
    status: ApplicationStatus | None,
    assigned_to: int | None,
) -> dict:
    filters = ApplicationFilters(
        date_from=date_from, date_to=date_to, application_type=application_type, status=status, assigned_to=assigned_to
    )
    repo = ApplicationRepository(db)
    items, total = await repo.list_paginated(filters, page=1, page_size=10_000)

    counts = {s.value: 0 for s in ApplicationStatus}
    critical = 0
    durations_seconds: list[float] = []
    for app in items:
        counts[app.status.value] += 1
        if app.priority.value == "CRITICAL":
            critical += 1
        if app.status == ApplicationStatus.COMPLETED:
            durations_seconds.append((app.updated_at - app.created_at).total_seconds())

    avg_seconds = sum(durations_seconds) / len(durations_seconds) if durations_seconds else 0

    return {
        "total": total,
        "new": counts[ApplicationStatus.NEW.value],
        "in_progress": counts[ApplicationStatus.IN_PROGRESS.value],
        "completed": counts[ApplicationStatus.COMPLETED.value],
        "rejected": counts[ApplicationStatus.REJECTED.value],
        "critical": critical,
        "avg_processing_hours": round(avg_seconds / 3600, 2),
        "items": items,
    }


@router.get("")
async def get_report(
    date_from: date | None = None,
    date_to: date | None = None,
    application_type: ApplicationType | None = None,
    status: ApplicationStatus | None = None,
    assigned_to: int | None = None,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_any_admin),
):
    report = await _build_report(db, date_from, date_to, application_type, status, assigned_to)
    report.pop("items")
    return report


@router.get("/export.csv")
async def export_csv(
    date_from: date | None = None,
    date_to: date | None = None,
    application_type: ApplicationType | None = None,
    status: ApplicationStatus | None = None,
    assigned_to: int | None = None,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_any_admin),
):
    report = await _build_report(db, date_from, date_to, application_type, status, assigned_to)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["№", "Дата", "Дербес шот", "Түрі", "Статус", "Приоритет", "Орындаушы"])
    for app in report["items"]:
        writer.writerow(
            [
                app.application_number,
                app.created_at.strftime("%Y-%m-%d %H:%M"),
                app.personal_account,
                app.application_type.value,
                app.status.value,
                app.priority.value,
                app.assigned_admin.name if app.assigned_admin else "",
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=report.csv"},
    )


@router.get("/export.xlsx")
async def export_xlsx(
    date_from: date | None = None,
    date_to: date | None = None,
    application_type: ApplicationType | None = None,
    status: ApplicationStatus | None = None,
    assigned_to: int | None = None,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_any_admin),
):
    report = await _build_report(db, date_from, date_to, application_type, status, assigned_to)
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    ws.append(["№", "Дата", "Дербес шот", "Түрі", "Статус", "Приоритет", "Орындаушы"])
    for app in report["items"]:
        ws.append(
            [
                app.application_number,
                app.created_at.strftime("%Y-%m-%d %H:%M"),
                app.personal_account,
                app.application_type.value,
                app.status.value,
                app.priority.value,
                app.assigned_admin.name if app.assigned_admin else "",
            ]
        )
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=report.xlsx"},
    )
