from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.rate_limit import limiter
from app.database import get_db
from app.schemas.auth import AdminOut, LoginRequest, TokenResponse
from app.services.audit_service import log_action
from app.services.auth_service import authenticate_admin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    admin, token = await authenticate_admin(db, payload.email, payload.password)
    await log_action(
        db,
        admin_id=admin.id,
        action="LOGIN",
        entity="admin",
        entity_id=str(admin.id),
        ip_address=request.client.host if request.client else None,
    )
    return TokenResponse(access_token=token, admin=AdminOut.model_validate(admin))


@router.get("/me", response_model=AdminOut)
async def me(admin=Depends(get_current_admin)) -> AdminOut:
    return AdminOut.model_validate(admin)
