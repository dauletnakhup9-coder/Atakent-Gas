from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.models.application import Application
from app.models.application_file import ApplicationFile
from app.models.application_history import ApplicationHistory
from app.models.enums import ApplicationStatus, ApplicationType, Priority
from app.repositories.admin_repo import AdminRepository
from app.repositories.application_repo import ApplicationRepository
from app.repositories.user_repo import UserRepository
from app.schemas.application import BotCreateApplicationRequest
from app.services import file_service, notification_service, realtime
from app.services.validators import validate_requested_date, verify_personal_account


def _priority_for(application_type: ApplicationType) -> Priority:
    return Priority.CRITICAL if application_type == ApplicationType.GAS_LEAK else Priority.NORMAL


def _generate_application_number(application_id: int, created_at: datetime) -> str:
    return f"REQ-{created_at:%Y%m%d}-{application_id:05d}"


async def create_application_from_bot(db: AsyncSession, payload: BotCreateApplicationRequest) -> Application:
    if not verify_personal_account(payload.personal_account):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Дербес шот форматы дұрыс емес")

    if payload.application_type == ApplicationType.MPI_REMOVAL:
        if payload.requested_date is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Күн көрсетілмеген")
        ok, err = validate_requested_date(payload.requested_date)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    if payload.application_type == ApplicationType.METER_NOT_WORKING:
        if not any(f.file_type.value == "METER_PHOTO" for f in payload.files):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Есептеу құралының фотосы қажет")
        if payload.latitude is None or payload.longitude is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Геолокация қажет")

    if payload.application_type == ApplicationType.GAS_LEAK:
        types_present = {f.file_type.value for f in payload.files}
        if "METER_PHOTO" not in types_present or "GAS_LEAK_PHOTO" not in types_present:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Екі фото да (құрал және газ шығу орны) қажет"
            )
        if payload.latitude is None or payload.longitude is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Геолокация қажет")

    user_repo = UserRepository(db)
    user = await user_repo.get_or_create(
        telegram_user_id=payload.user.telegram_user_id,
        telegram_username=payload.user.telegram_username,
        first_name=payload.user.first_name,
        last_name=payload.user.last_name,
    )

    application = Application(
        application_number="PENDING",
        user_id=user.id,
        personal_account=payload.personal_account,
        application_type=payload.application_type,
        status=ApplicationStatus.NEW,
        priority=_priority_for(payload.application_type),
        requested_date=payload.requested_date,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(application)
    await db.flush()

    application.application_number = _generate_application_number(application.id, application.created_at)

    for f in payload.files:
        storage_url = await file_service.fetch_validate_and_store_telegram_photo(
            application.application_number, f.telegram_file_id
        )
        db.add(
            ApplicationFile(
                application_id=application.id,
                file_type=f.file_type,
                telegram_file_id=f.telegram_file_id,
                storage_url=storage_url,
            )
        )

    db.add(
        ApplicationHistory(
            application_id=application.id,
            admin_id=None,
            old_status=None,
            new_status=ApplicationStatus.NEW,
            comment="Telegram bot арқылы құрылды",
        )
    )

    await db.commit()

    repo = ApplicationRepository(db)
    full = await repo.get_by_id(application.id)

    await realtime.publish_event(
        "application_created",
        {
            "id": full.id,
            "application_number": full.application_number,
            "application_type": full.application_type.value,
            "priority": full.priority.value,
            "status": full.status.value,
            "personal_account": full.personal_account,
            "created_at": full.created_at,
        },
    )
    return full


async def change_status(
    db: AsyncSession, application_id: int, new_status: ApplicationStatus, comment: str | None, admin: Admin
) -> Application:
    repo = ApplicationRepository(db)
    application = await repo.get_by_id(application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Өтінім табылмады")

    old_status = application.status
    application.status = new_status
    if comment:
        application.admin_comment = comment

    db.add(
        ApplicationHistory(
            application_id=application.id,
            admin_id=admin.id,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
        )
    )
    await db.commit()
    await db.refresh(application)

    await notification_service.notify_status_change(
        application.user.telegram_user_id, application.application_number, new_status, comment
    )
    await realtime.publish_event(
        "application_status_changed",
        {"id": application.id, "application_number": application.application_number, "status": new_status.value},
    )
    return application


async def assign_admin(db: AsyncSession, application_id: int, admin_id: int, actor: Admin) -> Application:
    repo = ApplicationRepository(db)
    application = await repo.get_by_id(application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Өтінім табылмады")

    admin_repo = AdminRepository(db)
    target_admin = await admin_repo.get_by_id(admin_id)
    if target_admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Қызметкер табылмады")

    application.assigned_to = admin_id
    db.add(
        ApplicationHistory(
            application_id=application.id,
            admin_id=actor.id,
            old_status=application.status,
            new_status=application.status,
            comment=f"Тағайындалды: {target_admin.name}",
        )
    )
    await db.commit()
    await db.refresh(application)

    await realtime.publish_event(
        "application_assigned",
        {"id": application.id, "application_number": application.application_number, "assigned_to": admin_id},
    )
    return application


async def add_comment(db: AsyncSession, application_id: int, comment: str, admin: Admin) -> Application:
    repo = ApplicationRepository(db)
    application = await repo.get_by_id(application_id)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Өтінім табылмады")

    application.admin_comment = comment
    db.add(
        ApplicationHistory(
            application_id=application.id,
            admin_id=admin.id,
            old_status=application.status,
            new_status=application.status,
            comment=comment,
        )
    )
    await db.commit()
    await db.refresh(application)
    return application
