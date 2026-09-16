from datetime import date
from typing import Any

import httpx

from bot.config import get_settings

settings = get_settings()


class BackendApiError(Exception):
    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Backend API error {status_code}: {detail}")


def _headers() -> dict:
    return {"X-Internal-Api-Key": settings.BOT_INTERNAL_API_KEY}


async def _request(method: str, path: str, **kwargs) -> Any:
    async with httpx.AsyncClient(base_url=settings.BACKEND_API_BASE_URL, timeout=30) as client:
        resp = await client.request(method, path, headers=_headers(), **kwargs)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail")
            except Exception:
                detail = resp.text
            raise BackendApiError(resp.status_code, detail)
        return resp.json()


async def create_application(
    telegram_user_id: int,
    telegram_username: str | None,
    first_name: str | None,
    last_name: str | None,
    personal_account: str,
    application_type: str,
    requested_date: date | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    files: list[dict] | None = None,
) -> dict:
    payload = {
        "user": {
            "telegram_user_id": telegram_user_id,
            "telegram_username": telegram_username,
            "first_name": first_name,
            "last_name": last_name,
        },
        "personal_account": personal_account,
        "application_type": application_type,
        "requested_date": requested_date.isoformat() if requested_date else None,
        "latitude": latitude,
        "longitude": longitude,
        "files": files or [],
    }
    return await _request("POST", "/bot/applications", json=payload)


async def get_my_applications(telegram_user_id: int) -> list[dict]:
    return await _request("GET", "/bot/applications/my", params={"telegram_user_id": telegram_user_id})


async def get_application_by_number(application_number: str) -> dict:
    return await _request("GET", f"/bot/applications/by-number/{application_number}")


async def get_bot_settings() -> dict:
    return await _request("GET", "/bot/settings")
