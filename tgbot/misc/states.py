from aiogram.dispatcher.filters.state import StatesGroup, State


class RegisterState(StatesGroup):
    phone = State()


class DeleteState(StatesGroup):
    phone = State()
