from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Безнал'),
            KeyboardButton(text='Нал / Безнал')
        ]
    ],
    resize_keyboard=True
)
