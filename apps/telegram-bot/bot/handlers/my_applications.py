import logging

from aiogram import F, Router
from aiogram.types import Message

from bot import texts
from bot.services.api_client import BackendApiError, get_my_applications

router = Router(name="my_applications")
logger = logging.getLogger(__name__)


@router.message(F.text == texts.MAIN_MENU_MY_REQUESTS)
async def my_applications(message: Message) -> None:
    try:
        applications = await get_my_applications(message.from_user.id)
    except BackendApiError:
        logger.exception("Failed to fetch applications for user %s", message.from_user.id)
        await message.answer(texts.SOMETHING_WENT_WRONG)
        return

    if not applications:
        await message.answer(texts.MY_REQUESTS_EMPTY)
        return

    lines = [texts.MY_REQUESTS_TITLE, ""]
    for app in applications[:10]:
        type_label = texts.TYPE_LABELS.get(app["application_type"], app["application_type"])
        status_label = texts.STATUS_LABELS.get(app["status"], app["status"])
        created = app["created_at"][:10]
        lines.append(f"{app['application_number']}\n{type_label} | {created}\n{status_label}\n")

    await message.answer("\n".join(lines))
