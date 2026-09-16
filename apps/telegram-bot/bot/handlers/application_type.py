from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.keyboards.application_type import (
    CB_GAS_LEAK,
    CB_METER_NOT_WORKING,
    CB_MPI_REMOVAL,
    application_type_keyboard,
)
from bot.keyboards.common import back_cancel_keyboard
from bot.states.application_states import GasLeakFlowStates, MeterFlowStates, MpiFlowStates, TypeSelectionStates

router = Router(name="application_type")


async def show_application_type_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(TypeSelectionStates.selecting)
    await message.answer(texts.CHOOSE_APPLICATION_TYPE, reply_markup=application_type_keyboard())


@router.callback_query(TypeSelectionStates.selecting)
async def select_application_type(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = callback.data

    if data == CB_METER_NOT_WORKING:
        await state.update_data(application_type="METER_NOT_WORKING")
        await state.set_state(MeterFlowStates.waiting_photo)
        await callback.message.answer(texts.ASK_METER_PHOTO, reply_markup=back_cancel_keyboard())

    elif data == CB_MPI_REMOVAL:
        await state.update_data(application_type="MPI_REMOVAL")
        await state.set_state(MpiFlowStates.waiting_date)
        await callback.message.answer(texts.ASK_MPI_DATE, reply_markup=back_cancel_keyboard())

    elif data == CB_GAS_LEAK:
        await state.update_data(application_type="GAS_LEAK")
        await state.set_state(GasLeakFlowStates.waiting_meter_photo)
        await callback.message.answer(texts.GAS_LEAK_WARNING)

        from bot.services.api_client import get_bot_settings

        try:
            settings_data = await get_bot_settings()
            phone = settings_data.get("emergency_phone", "104")
        except Exception:
            phone = "104"
        await callback.message.answer(texts.gas_leak_emergency_phone_text(phone))
        await callback.message.answer(texts.ASK_GAS_METER_PHOTO, reply_markup=back_cancel_keyboard())
