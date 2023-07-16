from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message


order_types = ['fix__confirm', 'taximeter__confirm', 'back__cancel']


def order_processing(amount):
    """Клавиатура для работы с заказами."""
    order_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=amount[0], callback_data='fix__confirm')],
            [InlineKeyboardButton(text=amount[1], callback_data='taximeter__confirm')],
            [InlineKeyboardButton(text='Отмена', callback_data='back__cancel')]
        ]
    )
    return order_keyboard


cancel_order_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='Да', callback_data='cancel_confirm'),
            InlineKeyboardButton(text='Нет', callback_data='not_cancel')
        ]
    ]
)


callback_unpaid = ['unpaid_today', 'unpaid_yesterday', 'unpaid_week', 'unpaid_month']
unpaid_orders_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
            [InlineKeyboardButton(text='За сегодня', callback_data='unpaid_today')],
            [InlineKeyboardButton(text='За вчера', callback_data='unpaid_yesterday')],
            [InlineKeyboardButton(text='За неделю', callback_data='unpaid_week')],
            [InlineKeyboardButton(text='За месяц', callback_data='unpaid_month')],
            [InlineKeyboardButton(text='Отмена', callback_data='unpaid_cancel')]
    ]
)


callback_earnings = ['earnings_today', 'earnings_yesterday', 'earnings_week', 'earnings_month']
earnings_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='За сегодня', callback_data='earnings_today')],
        [InlineKeyboardButton(text='За вчера', callback_data='earnings_yesterday')],
        [InlineKeyboardButton(text='За неделю', callback_data='earnings_week')],
        [InlineKeyboardButton(text='За месяц', callback_data='earnings_month')],
        [InlineKeyboardButton(text='Отмена', callback_data='earnings_cancel')]
    ]
)