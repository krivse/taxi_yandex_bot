from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from tgbot.models.query import access_debt_mode, add_or_update_limit_user, delete_access_user


async def choose_menu_for_user(session, telegram_id):
    """Выбриается клавиатура для пользователя с учетом его настроек."""
    access = await access_debt_mode(session, telegram_id)

    # если водителю не разрешена смена в долг, поле access_limit
    if access is None or not access[0]:
        menu = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Безнал'),
                    KeyboardButton(text='Нал / Безнал'),
                ]
            ],
            resize_keyboard=True
        )
        return menu

    # если водителю разрешена смена в долг, поле access_limit
    elif access[0]:
        menu_plus = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='Безнал'),
                    KeyboardButton(text='Нал / Безнал'),
                    KeyboardButton(text='Смена в долг')
                ]
            ],
            resize_keyboard=True
        )
        return menu_plus
