import logging

from aiogram import F, Router
from aiogram.types import Message

from bot import texts
from bot.services.api_client import BackendApiError, get_bot_settings

router = Router(name="contact")
logger = logging.getLogger(__name__)


@router.message(F.text == texts.MAIN_MENU_CONTACT)
async def contact(message: Message) -> None:
    try:
        settings_data = await get_bot_settings()
    except BackendApiError:
        logger.exception("Failed to fetch settings for contact info")
        await message.answer(texts.SOMETHING_WENT_WRONG)
        return

    await message.answer(
        texts.contact_text(
            settings_data.get("organization_name", "Газ қызметі"),
            settings_data.get("contact_phone", ""),
            settings_data.get("emergency_phone", ""),
        )
    )
