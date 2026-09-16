from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.auth.rbac import require_any_admin, require_dispatcher_or_above
from app.database import get_db
from app.models.admin import Admin
from app.models.enums import ApplicationStatus, ApplicationType, Priority
from app.repositories.application_repo import ApplicationFilters, ApplicationRepository
from app.schemas.application import (
    ApplicationDetailOut,
    ApplicationListOut,
    AssignRequest,
    CommentRequest,
    StatusUpdateRequest,
)
from app.services import application_service
from app.services.audit_service import log_action

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=ApplicationListOut)
async def list_applications(
    personal_account: str | None = None,
    application_number: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    application_type: ApplicationType | None = None,
    status: ApplicationStatus | None = None,
    priority: Priority | None = None,
    assigned_to: int | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|application_number|priority|status)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_any_admin),
) -> ApplicationListOut:
    filters = ApplicationFilters(
        personal_account=personal_account,
        application_number=application_number,
        date_from=date_from,
        date_to=date_to,
        application_type=application_type,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        search=search,
    )
    repo = ApplicationRepository(db)
    items, total = await repo.list_paginated(filters, page, page_size, sort_by, sort_dir)
    return ApplicationListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{application_id}", response_model=ApplicationDetailOut)
async def get_application(
    application_id: int, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_any_admin)
) -> ApplicationDetailOut:
    repo = ApplicationRepository(db)
    application = await repo.get_by_id(application_id)
    if application is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Өтінім табылмады")
    return application


@router.patch("/{application_id}/status", response_model=ApplicationDetailOut)
async def update_status(
    application_id: int,
    payload: StatusUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_any_admin),
) -> ApplicationDetailOut:
    application = await application_service.change_status(
        db, application_id, payload.status, payload.comment, admin
    )
    await log_action(
        db,
        admin_id=admin.id,
        action="STATUS_CHANGE",
        entity="application",
        entity_id=str(application_id),
        ip_address=request.client.host if request.client else None,
        details=f"-> {payload.status.value}",
    )
    repo = ApplicationRepository(db)
    return await repo.get_by_id(application_id)


@router.patch("/{application_id}/assign", response_model=ApplicationDetailOut)
async def assign_application(
    application_id: int,
    payload: AssignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_dispatcher_or_above),
) -> ApplicationDetailOut:
    await application_service.assign_admin(db, application_id, payload.admin_id, admin)
    await log_action(
        db,
        admin_id=admin.id,
        action="ASSIGN",
        entity="application",
        entity_id=str(application_id),
        ip_address=request.client.host if request.client else None,
        details=f"-> admin {payload.admin_id}",
    )
    repo = ApplicationRepository(db)
    return await repo.get_by_id(application_id)


@router.post("/{application_id}/comments", response_model=ApplicationDetailOut)
async def add_comment(
    application_id: int,
    payload: CommentRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_any_admin),
) -> ApplicationDetailOut:
    await application_service.add_comment(db, application_id, payload.comment, admin)
    repo = ApplicationRepository(db)
    return await repo.get_by_id(application_id)


@router.get("/{application_id}/history")
async def get_history(
    application_id: int, db: AsyncSession = Depends(get_db), admin: Admin = Depends(require_any_admin)
):
    repo = ApplicationRepository(db)
    application = await repo.get_by_id(application_id)
    if application is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Өтінім табылмады")
    return [
        {
            "id": h.id,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "comment": h.comment,
            "admin_name": h.admin.name if h.admin else None,
            "created_at": h.created_at,
        }
        for h in application.history
    ]
