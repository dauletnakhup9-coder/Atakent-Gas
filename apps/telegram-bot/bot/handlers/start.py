from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot import texts
from bot.keyboards.common import account_confirm_keyboard, cancel_only_keyboard, main_menu_keyboard
from bot.states.application_states import AccountStates

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.WELCOME, reply_markup=cancel_only_keyboard())
    await state.set_state(AccountStates.waiting_account)


@router.message(F.text == texts.MAIN_MENU_NEW_REQUEST)
async def new_request_from_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(AccountStates.waiting_account)
    await message.answer(texts.WELCOME, reply_markup=cancel_only_keyboard())


@router.message(AccountStates.waiting_account, F.text)
async def receive_account(message: Message, state: FSMContext) -> None:
    from bot.services.validators import is_valid_account_format

    account = message.text.strip()
    if not is_valid_account_format(account):
        await message.answer(texts.INVALID_ACCOUNT_FORMAT)
        return

    await state.update_data(account=account)
    await state.set_state(AccountStates.confirm_account)
    await message.answer(texts.confirm_account_text(account), reply_markup=account_confirm_keyboard())


@router.message(AccountStates.confirm_account, F.text == texts.CONFIRM_EDIT)
async def edit_account(message: Message, state: FSMContext) -> None:
    await state.set_state(AccountStates.waiting_account)
    await message.answer(texts.ASK_ACCOUNT_AGAIN, reply_markup=cancel_only_keyboard())


@router.message(AccountStates.confirm_account, F.text == texts.CONFIRM_CORRECT)
async def confirm_account(message: Message, state: FSMContext) -> None:
    from bot.handlers.application_type import show_application_type_menu

    await show_application_type_menu(message, state)
