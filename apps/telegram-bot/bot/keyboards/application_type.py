from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import texts

CB_METER_NOT_WORKING = "app_type:METER_NOT_WORKING"
CB_MPI_REMOVAL = "app_type:MPI_REMOVAL"
CB_GAS_LEAK = "app_type:GAS_LEAK"


def application_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.TYPE_METER_NOT_WORKING, callback_data=CB_METER_NOT_WORKING)],
            [InlineKeyboardButton(text=texts.TYPE_MPI_REMOVAL, callback_data=CB_MPI_REMOVAL)],
            [InlineKeyboardButton(text=texts.TYPE_GAS_LEAK, callback_data=CB_GAS_LEAK)],
        ]
    )
