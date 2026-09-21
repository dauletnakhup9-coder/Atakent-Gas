import hashlib
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import get_db, utcnow
from app.models import Admin, AdminSession, Role

password_hasher = PasswordHash.recommended()
DUMMY_HASH = password_hasher.hash(secrets.token_urlsafe(32))
redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
RATE_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return count
"""


async def rate_limit(key: str, limit: int, seconds: int):
    try:
        count = await redis.eval(RATE_SCRIPT, 1, f"rate:{key}", seconds)
    except Exception as exc:
        raise HTTPException(503, "Қызмет уақытша қолжетімсіз") from exc
    if count > limit:
        raise HTTPException(429, "Сұраныс тым көп. Кейінірек қайталаңыз.", headers={"Retry-After": str(seconds)})


def check_origin(request: Request):
    if request.headers.get("origin", "").rstrip("/") not in get_settings().origins:
        raise HTTPException(403, "Origin rejected")


async def current_admin(request: Request, db: AsyncSession = Depends(get_db)) -> Admin:
    token = request.cookies.get("session", "")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    record = (
        await db.execute(
            select(AdminSession, Admin)
            .join(Admin)
            .where(AdminSession.token_hash == token_hash, AdminSession.expires_at > utcnow(), Admin.active.is_(True))
        )
    ).first()
    if not record:
        raise HTTPException(401, "Қайта кіріңіз")
    session, admin = record
    request.state.session = session
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        check_origin(request)
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf_token):
            raise HTTPException(403, "CSRF rejected")
    await rate_limit(f"admin:{admin.id}", 240, 60)
    return admin


def roles(*allowed: Role):
    async def dependency(admin: Admin = Depends(current_admin)):
        if admin.role not in allowed:
            raise HTTPException(403, "Құқық жеткіліксіз")
        return admin

    return dependency


managers = roles(Role.SUPER_ADMIN, Role.DISPATCHER)
super_admin = roles(Role.SUPER_ADMIN)


async def bot_auth(request: Request):
    if not secrets.compare_digest(request.headers.get("x-bot-key", ""), get_settings().bot_api_key):
        raise HTTPException(401, "Service authentication required")


async def create_session(db, admin):
    token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    db.add(
        AdminSession(
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            admin_id=admin.id,
            csrf_token=csrf,
            expires_at=utcnow() + timedelta(hours=get_settings().session_hours),
        )
    )
    return token, csrf
