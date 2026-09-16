from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_bot_internal_key
from app.core.rate_limit import limiter
from app.database import get_db
from app.repositories.application_repo import ApplicationRepository
from app.repositories.user_repo import UserRepository
from app.schemas.application import ApplicationDetailOut, BotCreateApplicationRequest
from app.services import application_service
from app.services.settings_service import get_all_settings
from app.services.validators import verify_personal_account

router = APIRouter(prefix="/bot", tags=["bot-internal"], dependencies=[Depends(verify_bot_internal_key)])


@router.post("/applications", response_model=ApplicationDetailOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def bot_create_application(
    request: Request, payload: BotCreateApplicationRequest, db: AsyncSession = Depends(get_db)
) -> ApplicationDetailOut:
    return await application_service.create_application_from_bot(db, payload)


@router.get("/applications/verify-account")
async def verify_account(account_number: str):
    return {"valid": verify_personal_account(account_number)}


@router.get("/applications/my")
async def my_applications(telegram_user_id: int, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_telegram_id(telegram_user_id)
    if user is None:
        return []
    repo = ApplicationRepository(db)
    apps = await repo.list_by_user(user.id)
    return [
        {
            "application_number": a.application_number,
            "application_type": a.application_type.value,
            "status": a.status.value,
            "priority": a.priority.value,
            "created_at": a.created_at,
        }
        for a in apps
    ]


@router.get("/applications/by-number/{application_number}")
async def get_by_number(application_number: str, db: AsyncSession = Depends(get_db)):
    repo = ApplicationRepository(db)
    application = await repo.get_by_number(application_number)
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Өтінім табылмады")
    return {
        "application_number": application.application_number,
        "application_type": application.application_type.value,
        "status": application.status.value,
        "priority": application.priority.value,
        "admin_comment": application.admin_comment,
        "created_at": application.created_at,
    }


@router.get("/settings")
async def bot_settings(db: AsyncSession = Depends(get_db)):
    return await get_all_settings(db)
