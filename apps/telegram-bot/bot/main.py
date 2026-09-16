import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from bot.config import get_settings
from bot.handlers import (
    application_type,
    contact,
    gas_leak_flow,
    meter_flow,
    mpi_flow,
    my_applications,
    navigation,
    start,
)
from bot.middlewares.throttling import ThrottlingMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")


def build_storage():
    settings = get_settings()
    if settings.USE_REDIS_FSM_STORAGE:
        try:
            return RedisStorage.from_url(settings.REDIS_URL)
        except Exception:
            logger.exception("Failed to connect to Redis, falling back to in-memory FSM storage")
    return MemoryStorage()


async def main() -> None:
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=build_storage())

    dp.message.middleware(ThrottlingMiddleware())

    # Order matters: navigation (global cancel) must be checked before flow-specific routers.
    dp.include_router(navigation.router)
    dp.include_router(start.router)
    dp.include_router(application_type.router)
    dp.include_router(meter_flow.router)
    dp.include_router(mpi_flow.router)
    dp.include_router(gas_leak_flow.router)
    dp.include_router(my_applications.router)
    dp.include_router(contact.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
