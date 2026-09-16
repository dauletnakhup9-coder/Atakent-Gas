from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting

DEFAULT_SETTINGS: dict[str, str] = {
    "organization_name": "Газ қызметі",
    "contact_phone": "+7 700 000 00 00",
    "emergency_phone": "104",
    "max_photo_size_mb": "10",
    "notification_new": "🆕 {number} өтініміңіз тіркелді.",
    "notification_in_progress": "🟡 {number} өтініміңіз өңдеуге алынды.",
    "notification_completed": "✅ {number} өтініміңіз орындалды.",
    "notification_rejected": "❌ {number} өтініміңіз қабылданбады.",
}

SUPER_ADMIN_ONLY_KEYS = {"max_photo_size_mb", "emergency_phone"}


async def get_all_settings(db: AsyncSession) -> dict[str, str]:
    result = await db.execute(select(SystemSetting))
    stored = {row.key: row.value for row in result.scalars().all()}
    merged = dict(DEFAULT_SETTINGS)
    merged.update(stored)
    return merged


async def update_settings(db: AsyncSession, values: dict[str, str]) -> dict[str, str]:
    for key, value in values.items():
        existing = await db.get(SystemSetting, key)
        if existing:
            existing.value = value
        else:
            db.add(SystemSetting(key=key, value=value))
    await db.commit()
    return await get_all_settings(db)
