from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from bot import texts


def account_confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.CONFIRM_CORRECT), KeyboardButton(text=texts.CONFIRM_EDIT)]],
        resize_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.MAIN_MENU_NEW_REQUEST)],
            [KeyboardButton(text=texts.MAIN_MENU_MY_REQUESTS), KeyboardButton(text=texts.MAIN_MENU_CONTACT)],
        ],
        resize_keyboard=True,
    )


def location_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.SEND_LOCATION_BUTTON, request_location=True)],
            [KeyboardButton(text=texts.BACK), KeyboardButton(text=texts.CANCEL)],
        ],
        resize_keyboard=True,
    )


def cancel_only_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=texts.CANCEL)]], resize_keyboard=True)


def back_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.BACK), KeyboardButton(text=texts.CANCEL)]],
        resize_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
