from aiogram.dispatcher.filters.state import StatesGroup, State


class RegisterState(StatesGroup):
    phone = State()


class DeleteState(StatesGroup):
    phone = State()


class EditState(StatesGroup):
    on_phone = State()
    off_phone = State()
    limit = State()


class NewSendState(StatesGroup):
    text = State()


class CodeConfirmState(StatesGroup):
    code = State()


class AccountParkState(StatesGroup):
    password = State()


class HelpState(StatesGroup):
    text = State()
