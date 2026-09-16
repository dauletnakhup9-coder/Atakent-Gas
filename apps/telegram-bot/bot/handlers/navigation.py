from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot import texts
from bot.keyboards.common import main_menu_keyboard

router = Router(name="navigation")


@router.message(F.text == texts.CANCEL)
async def cancel_any_flow(message: Message, state: FSMContext) -> None:
    await state.set_state(None)
    await state.update_data(
        application_type=None,
        meter_photo_file_id=None,
        gas_meter_photo_file_id=None,
        gas_leak_photo_file_id=None,
        latitude=None,
        longitude=None,
        requested_date=None,
    )
    data = await state.get_data()
    if data.get("account"):
        await message.answer(texts.CANCELLED, reply_markup=main_menu_keyboard())
    else:
        await message.answer(texts.CANCELLED)
