from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

access = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Добавить', callback_data='add'),
            InlineKeyboardButton(text='Отклонить', callback_data='reject')
        ]
    ]
)

reset_user_removal = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel')
        ]
    ]
)


access_debt = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Включить', callback_data='on_debt'),
            InlineKeyboardButton(text='Отключить', callback_data='off_debt')
        ],
        [
            InlineKeyboardButton(text='Отмена', callback_data='cancel_debt')
        ]
    ]
)

agree_text = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Отправить', callback_data='agree_send'),
            InlineKeyboardButton(text='Отменить', callback_data='cancel_send')
        ],
    ]
)

account = InlineKeyboardMarkup(
 inline_keyboard=[
        [
            InlineKeyboardButton(text='Отменить', callback_data='cancel_password')
        ],
    ]
)

help_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data='confirm_help'),
            InlineKeyboardButton(text='Нет', callback_data='cancel_help')
        ]
    ]
)
