from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot import texts


def meter_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.CONFIRM_SEND)],
            [KeyboardButton(text=texts.CONFIRM_EDIT), KeyboardButton(text=texts.CANCEL)],
        ],
        resize_keyboard=True,
    )


def mpi_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.CONFIRM_SEND)],
            [KeyboardButton(text=texts.CONFIRM_EDIT_DATE), KeyboardButton(text=texts.CANCEL)],
        ],
        resize_keyboard=True,
    )


def gas_leak_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.CONFIRM_SEND_URGENT)],
            [KeyboardButton(text=texts.CONFIRM_EDIT), KeyboardButton(text=texts.CANCEL)],
        ],
        resize_keyboard=True,
    )
