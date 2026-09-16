from aiogram.fsm.state import State, StatesGroup


class AccountStates(StatesGroup):
    waiting_account = State()
    confirm_account = State()


class TypeSelectionStates(StatesGroup):
    selecting = State()


class MeterFlowStates(StatesGroup):
    waiting_photo = State()
    waiting_location = State()
    confirm = State()


class MpiFlowStates(StatesGroup):
    waiting_date = State()
    confirm = State()


class GasLeakFlowStates(StatesGroup):
    waiting_meter_photo = State()
    waiting_leak_photo = State()
    waiting_location = State()
    confirm = State()
