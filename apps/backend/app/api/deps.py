from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.config import get_settings
from app.database import get_db
from app.models.admin import Admin
from app.repositories.admin_repo import AdminRepository

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Авторизация қажет")
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    admin_id = payload.get("sub")
    repo = AdminRepository(db)
    admin = await repo.get_by_id(int(admin_id))
    if admin is None or not admin.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Аккаунт белсенді емес")
    return admin


async def verify_bot_internal_key(x_internal_api_key: str = Header(default="")) -> None:
    if not x_internal_api_key or x_internal_api_key != settings.BOT_INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal API key")
