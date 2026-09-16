import logging

import httpx

from app.config import get_settings
from app.models.enums import ApplicationStatus

settings = get_settings()
logger = logging.getLogger("notifications")

STATUS_MESSAGES = {
    ApplicationStatus.IN_PROGRESS: "🟡 {number} өтініміңіз өңдеуге алынды.",
    ApplicationStatus.COMPLETED: "✅ {number} өтініміңіз орындалды.",
    ApplicationStatus.REJECTED: "❌ {number} өтініміңіз қабылданбады.",
    ApplicationStatus.NEW: "🆕 {number} өтініміңіз тіркелді.",
}


async def notify_status_change(
    telegram_user_id: int, application_number: str, new_status: ApplicationStatus, comment: str | None
) -> None:
    if not settings.BOT_TOKEN:
        return
    template = STATUS_MESSAGES.get(new_status, "{number} өтініміңіздің мәртебесі өзгерді.")
    text = template.format(number=application_number)
    if comment:
        text += f"\n\nАдминистратордың пікірі: {comment}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.TELEGRAM_API_BASE}/bot{settings.BOT_TOKEN}/sendMessage",
                json={"chat_id": telegram_user_id, "text": text},
            )
            resp.raise_for_status()
    except Exception:
        logger.exception("Failed to notify telegram user %s about %s", telegram_user_id, application_number)
