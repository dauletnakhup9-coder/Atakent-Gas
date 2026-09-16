import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot import texts
from bot.keyboards.common import back_cancel_keyboard, main_menu_keyboard
from bot.keyboards.confirm import mpi_confirm_keyboard
from bot.services.api_client import BackendApiError, create_application
from bot.services.validators import parse_kk_date, validate_future_date
from bot.states.application_states import MpiFlowStates

router = Router(name="mpi_flow")
logger = logging.getLogger(__name__)


@router.message(MpiFlowStates.waiting_date, F.text == texts.BACK)
async def mpi_date_back(message: Message, state: FSMContext) -> None:
    from bot.handlers.application_type import show_application_type_menu

    await show_application_type_menu(message, state)


@router.message(MpiFlowStates.waiting_date, F.text)
async def receive_mpi_date(message: Message, state: FSMContext) -> None:
    parsed = parse_kk_date(message.text)
    if parsed is None:
        await message.answer(texts.INVALID_DATE_FORMAT)
        return

    ok, reason = validate_future_date(parsed)
    if not ok:
        await message.answer(texts.INVALID_DATE_PAST if reason == "past" else texts.INVALID_DATE_TOO_FAR)
        return

    await state.update_data(requested_date=parsed.isoformat())
    await state.set_state(MpiFlowStates.confirm)
    data = await state.get_data()
    await message.answer(
        texts.mpi_summary_text(data["account"], parsed.strftime("%d.%m.%Y")), reply_markup=mpi_confirm_keyboard()
    )


@router.message(MpiFlowStates.confirm, F.text == texts.CONFIRM_EDIT_DATE)
async def mpi_edit_date(message: Message, state: FSMContext) -> None:
    await state.update_data(requested_date=None)
    await state.set_state(MpiFlowStates.waiting_date)
    await message.answer(texts.ASK_MPI_DATE, reply_markup=back_cancel_keyboard())


@router.message(MpiFlowStates.confirm, F.text == texts.CONFIRM_SEND)
async def mpi_send(message: Message, state: FSMContext) -> None:
    from datetime import date

    data = await state.get_data()
    try:
        result = await create_application(
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            personal_account=data["account"],
            application_type="MPI_REMOVAL",
            requested_date=date.fromisoformat(data["requested_date"]),
        )
    except BackendApiError:
        logger.exception("Failed to create MPI_REMOVAL application")
        await message.answer(texts.SOMETHING_WENT_WRONG, reply_markup=main_menu_keyboard())
        await state.clear()
        return

    await state.clear()
    await state.update_data(account=data["account"])
    await message.answer(texts.success_text(result["application_number"]), reply_markup=main_menu_keyboard())
