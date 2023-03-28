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
