import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot import texts
from bot.keyboards.common import back_cancel_keyboard, location_request_keyboard, main_menu_keyboard
from bot.keyboards.confirm import gas_leak_confirm_keyboard
from bot.services.api_client import BackendApiError, create_application
from bot.states.application_states import GasLeakFlowStates

router = Router(name="gas_leak_flow")
logger = logging.getLogger(__name__)


@router.message(GasLeakFlowStates.waiting_meter_photo, F.text == texts.BACK)
async def gas_meter_photo_back(message: Message, state: FSMContext) -> None:
    from bot.handlers.application_type import show_application_type_menu

    await show_application_type_menu(message, state)


@router.message(GasLeakFlowStates.waiting_meter_photo, F.photo)
async def receive_gas_meter_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(gas_meter_photo_file_id=message.photo[-1].file_id)
    await state.set_state(GasLeakFlowStates.waiting_leak_photo)
    await message.answer(texts.ASK_GAS_LEAK_PHOTO, reply_markup=back_cancel_keyboard())


@router.message(GasLeakFlowStates.waiting_meter_photo)
async def gas_meter_photo_invalid(message: Message) -> None:
    await message.answer(texts.NOT_A_PHOTO)


@router.message(GasLeakFlowStates.waiting_leak_photo, F.text == texts.BACK)
async def gas_leak_photo_back(message: Message, state: FSMContext) -> None:
    await state.update_data(gas_meter_photo_file_id=None)
    await state.set_state(GasLeakFlowStates.waiting_meter_photo)
    await message.answer(texts.ASK_GAS_METER_PHOTO, reply_markup=back_cancel_keyboard())


@router.message(GasLeakFlowStates.waiting_leak_photo, F.photo)
async def receive_gas_leak_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(gas_leak_photo_file_id=message.photo[-1].file_id)
    await state.set_state(GasLeakFlowStates.waiting_location)
    await message.answer(texts.ASK_LOCATION, reply_markup=location_request_keyboard())


@router.message(GasLeakFlowStates.waiting_leak_photo)
async def gas_leak_photo_invalid(message: Message) -> None:
    await message.answer(texts.NOT_A_PHOTO)


@router.message(GasLeakFlowStates.waiting_location, F.text == texts.BACK)
async def gas_leak_location_back(message: Message, state: FSMContext) -> None:
    await state.update_data(gas_leak_photo_file_id=None)
    await state.set_state(GasLeakFlowStates.waiting_leak_photo)
    await message.answer(texts.ASK_GAS_LEAK_PHOTO, reply_markup=back_cancel_keyboard())


@router.message(GasLeakFlowStates.waiting_location, F.location)
async def receive_gas_leak_location(message: Message, state: FSMContext) -> None:
    await state.update_data(latitude=message.location.latitude, longitude=message.location.longitude)
    await state.set_state(GasLeakFlowStates.confirm)
    data = await state.get_data()
    await message.answer(texts.gas_leak_summary_text(data["account"]), reply_markup=gas_leak_confirm_keyboard())


@router.message(GasLeakFlowStates.waiting_location)
async def gas_leak_location_invalid(message: Message) -> None:
    await message.answer(texts.NOT_A_LOCATION)


@router.message(GasLeakFlowStates.confirm, F.text == texts.CONFIRM_EDIT)
async def gas_leak_edit(message: Message, state: FSMContext) -> None:
    await state.update_data(
        gas_meter_photo_file_id=None, gas_leak_photo_file_id=None, latitude=None, longitude=None
    )
    await state.set_state(GasLeakFlowStates.waiting_meter_photo)
    await message.answer(texts.ASK_GAS_METER_PHOTO, reply_markup=back_cancel_keyboard())


@router.message(GasLeakFlowStates.confirm, F.text == texts.CONFIRM_SEND_URGENT)
async def gas_leak_send(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        result = await create_application(
            telegram_user_id=message.from_user.id,
            telegram_username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            personal_account=data["account"],
            application_type="GAS_LEAK",
            latitude=data["latitude"],
            longitude=data["longitude"],
            files=[
                {"file_type": "METER_PHOTO", "telegram_file_id": data["gas_meter_photo_file_id"]},
                {"file_type": "GAS_LEAK_PHOTO", "telegram_file_id": data["gas_leak_photo_file_id"]},
            ],
        )
    except BackendApiError:
        logger.exception("Failed to create GAS_LEAK application")
        await message.answer(texts.SOMETHING_WENT_WRONG, reply_markup=main_menu_keyboard())
        await state.clear()
        return

    await state.clear()
    await state.update_data(account=data["account"])
    await message.answer(texts.success_text(result["application_number"]), reply_markup=main_menu_keyboard())
