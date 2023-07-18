from datetime import date
from datetime import timedelta

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher import FSMContext

from tgbot.keyboards.inline_users import callback_earnings, callback_unpaid, cancel_order_keyboard, earnings_keyboard, \
    order_types, unpaid_orders_keyboard
from tgbot.keyboards.user_button import choose_menu_for_user
from tgbot.misc.states import RegisterState
from tgbot.models.query import access_debt_mode, get_info_from_help, get_user
from tgbot.services.other_functions.conts import list_months
from tgbot.services.requests.earnings.setting_earning_driver import settings_for_select_period_earnings_driver
from tgbot.services.requests.limit.choose_payment_method import change_of_payment_method
from tgbot.services.requests.order.choose_order_method import change_working_order_method
from tgbot.services.requests.unpaid_orders.setting_up_unpaid_orders import settings_for_select_period_unpaid_orders
from tgbot.services.set_commands import set_default_commands


async def user_start(message: Message, session, state: FSMContext):
    """Реакция на команду /start и получение пользователя из БД."""
    # тг id пользователя
    telegram_id = message.chat.id
    user = await get_user(session, telegram_id)
    # команды для водителей.
    await set_default_commands(
        message.bot,
        user_id=message.from_id
    )

    if user is None:
        # приветственное сообщение для пользователя.
        await message.answer(f'{message.from_user.full_name}, вас приветствует бот Фартового парка.\n '
                             'Для авторизации в системе введите номер телефона как в Яндекс Про.')
        # Администратору в хендлер add_user будет отловлено состояние пользователя.
        await RegisterState.phone.set()
    elif user is not None:
        # выводится сообщение об выборе тарифа работы
        await message.answer(
            f'{user[0]} {user[1]}, выберите способ оплаты за заказы в Яндекс Про',
            reply_markup=await choose_menu_for_user(session, telegram_id)
        )
        await state.update_data(first_name=user[0], middle_name=user[1], taxi_id=user[2], phone=user[3])


async def payment_method(message: Message, session, state: FSMContext):
    """Выбор способа оплаты."""
    admin = message.bot.get('config').tg_bot.admin_ids[0]
    # название кнопки
    method = message.text

    # получаем пользователя из бд.
    first_name, middle_name, taxi_id, phone = None, None, None, None
    telegram_id = message.chat.id
    user = await get_user(session, telegram_id)
    if user is not None:
        first_name, middle_name, taxi_id, phone = user

    if method == '💳Безнал' and user is not None:
        # установка лимита для оплаты по безналу.
        response = await change_of_payment_method(message, session, '15000', str(phone), taxi_id)
        if response == 200:
            await message.answer(f'{first_name} {middle_name}, '
                                 'Вам установлен лимит 15000 руб. '
                                 'Пока Ваш баланс ниже этой суммы, вам будут поступать только БЕЗНАЛИЧНЫЕ заказы.')
        else:
            await message.answer('Ошибка запроса! Попробуйте позже..')
            await message.bot.send_message(
                chat_id=admin,
                text=f'Ошибка запроса при изменения лимита у {first_name} {middle_name}, ошибка: {response}')
    elif method == '💵Нал / Безнал' and user is not None:
        # установка лимита для оплаты по нал / безннал.
        response = await change_of_payment_method(message, session, '50', str(phone), taxi_id)
        if response == 200:
            await message.answer(f'{first_name} {middle_name}, '
                                 'Вам установлен лимит 50 руб. '
                                 'Теперь Вам будут поступать НАЛИЧНЫЕ и БЕЗНАЛИЧНЫЕ заказы.')
        else:
            await message.answer('Ошибка запроса! Попробуйте позже..')
            await message.bot.send_message(
                chat_id=admin,
                text=f'Ошибка запроса при изменения лимита у {first_name} {middle_name}, ошибка: {response}.')
    elif method == '🕰Смена в долг' and user is not None:
        # установка лимита для режима работы в долг.
        access, limit = await access_debt_mode(session, telegram_id)
        if access:
            response = await change_of_payment_method(message, session, str(limit), str(phone), taxi_id)
            if response == 200:
                await message.answer(f'{first_name} {middle_name}, '
                                     f'Вам установлен лимит {limit}, '
                                     'теперь Вы можете купить смену в долг.')
            else:
                await message.answer('Ошибка запроса! Попробуйте позже..')
                await message.bot.send_message(
                    chat_id=admin,
                    text=f'Ошибка запроса при изменения лимита у {first_name} {middle_name}, описание: {response}.')
        elif not access:
            await message.answer('Смена в долг не подключена!')
    else:
        await message.answer(f'У вас нет доступа!')
    # сбрасывается состояние пользователя.
    await state.finish()


async def amount_order(message: Message, session, state: FSMContext):
    """Получение суммы заказа"""
    if message.text != '🏁Завершить тек. заказ':
        await message.answer('Функция временно отключена!')
    else:
        telegram_id = message.chat.id
        user = await get_user(session, telegram_id)

        # В этой функции с помощью аргумента amount определим сумму текущего заказа
        if user is not None:
            msg_for_delete_current_order = await message.answer(text='🚖 Проверяю текущие заказы.. Подождите..')
            await state.update_data(msg_for_delete_current_order=msg_for_delete_current_order.message_id)
            await change_working_order_method(message, session, state, str(user[3]), user[2], way='amount', amount=True)
        else:
            await message.answer('У вас нет доступа!')


async def complete_order(call: CallbackQuery, session, state: FSMContext):
    """Выбор способа оплаты с последующим завершением / отмена действия."""

    # telegra_id пользователя
    telegram_id = call.message.chat.id
    user = await get_user(session, telegram_id)

    # выбор способа оплаты заказа
    if call.data == 'fix__confirm':
        await change_working_order_method(call, session, state, str(user[3]), user[2], way='fixed', amount=False)
        await call.answer('☺️Заказ перешёл в статус "Завершённые"')
    elif call.data == 'taximeter__confirm':
        await change_working_order_method(call, session, state, str(user[3]), user[2], way='taximeter', amount=False)
        await call.answer('☺️Заказ перешёл в статус "Завершённые"')
    elif call.data == 'back__cancel':
        await call.answer(
            text='Отмена действия по завершению заказа',
        )
    msg_delete = (await state.get_data()).get('msg_order_delete')
    await call.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_delete)
    await state.finish()


async def cancel_order(message: Message, session, state: FSMContext):
    """Отмена текущего заказа."""
    telegram_id = message.chat.id
    user = await get_user(session, telegram_id)
    if user is not None:
        await message.answer(
            text='При отмене заказа с Вас будут списаны баллы Активности. Отменить заказ?',
            reply_markup=cancel_order_keyboard
        )
    else:
        await message.answer(f'У вас нет доступа!')


async def confirm_cancel_order(call: CallbackQuery, session, state: FSMContext):
    """Подтверждение отмены заказа."""
    # если пользователь нажал не на команду, а сразу на кнопку, то будет запрос к БД.
    telegram_id = call.message.chat.id
    user = await get_user(session, telegram_id)

    if call.data == 'cancel_confirm' and user is not None:
        msg_for_delete_current_order = await call.message.answer(text='🚖 Проверяю текущие заказы.. Подождите..')
        await state.update_data(msg_for_delete_current_order=msg_for_delete_current_order.message_id)
        request = await change_working_order_method(
            call, session, state, str(user[3]), user[2], way='cancel_confirm', amount=False)
        await call.message.delete()
        if request.get('empty_order') is None:
            await call.answer('😥Текущий заказ отменен!')
    elif call.data == 'not_cancel' and user is not None:
        await call.message.delete()
        await call.answer(text='Текущий заказ не отменен!')
    else:
        await call.message.answer(f'У вас нет доступа!')
    await state.finish()


async def get_help(message: Message, session):
    """Получить условия службы такси."""
    text_help = (await get_info_from_help(session)).text

    await message.answer(text_help)


async def get_unpaid_orders(message: Message, session, state: FSMContext):
    """Генерация клавиатуры для выбора периода по неоплаченным заказам."""
    telegram_id = message.chat.id
    user = await get_user(session, telegram_id)
    if user is not None:
        msg_delete_unpaid = await message.answer(text='Выберите период для отображения неоплаченных заказов',
                                                 reply_markup=unpaid_orders_keyboard)
        await state.update_data(msg_delete_unpaid=msg_delete_unpaid.message_id)
    else:
        await message.answer(f'У вас нет доступа!')


async def select_period_unpaid_orders(call: CallbackQuery, session, state: FSMContext):
    """Выбор периода для получения информации о неоплаченных заказах."""
    admin = call.message.bot.get('config').tg_bot.admin_ids[0]
    # telegra_id пользователя
    telegram_id = call.message.chat.id
    user = await get_user(session, telegram_id)

    # отмена действий по функции заработка
    msg_for_delete = (await state.get_data()).get('msg_delete_unpaid')
    await call.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_for_delete)

    # сохраняем сегодняшнюю дату
    date_today = date.today()
    response = None
    date_last_month = date_today.replace(month=(date_today.replace(day=1) - timedelta(days=1)).month)
    period = {
        'unpaid_today': f'за сегодня: {date_today.strftime("%d.%m.%Y г.")}',
        'unpaid_yesterday': f'за вчерашний день: {(date_today - timedelta(days=1)).strftime("%d.%m.%Y г.")}',
        'unpaid_week':
            f'за неделю: с {(date_today - timedelta(weeks=1)).strftime("%d.%m.%Y г.")} '
            f'по {date_today.strftime("%d.%m.%Y г.")}',
        'unpaid_month':
            f'за месяц: с {date_last_month.strftime("%d.%m.%Y г.")} '
            f'по {date_today.strftime("%d.%m.%Y г.")}'
    }
    msg_del_unpaid = await call.message.answer(
        text=f'🔎 Поиск неоплаченных заказов {period.get(call.data)} Ожидайте..')

    if call.data == 'unpaid_today':
        day = str(date_today.day)
        month = date_today.month

        # интервал дат для календаря
        interval = {
            # импорт константы из tgbot.services.other_functions.conts
            'start_day': day, 'start_month': list_months.get(month),
            'end_day': day, 'end_month': list_months.get(month),
        }

        response = await settings_for_select_period_unpaid_orders(call, session, str(user[3]), user[2], interval)

    elif call.data == 'unpaid_yesterday':
        yesterday = str((date_today - timedelta(days=1)).day)
        month = date_today.month

        # интервал дат для календаря
        interval = {
            # импорт константы из tgbot.services.other_functions.conts
            'start_day': yesterday, 'start_month': list_months.get(month),
            'end_day': yesterday, 'end_month': list_months.get(month),
        }

        response = await settings_for_select_period_unpaid_orders(call, session, str(user[3]), user[2], interval)

    elif call.data == 'unpaid_week':
        response = await settings_for_select_period_unpaid_orders(call, session, str(user[3]), user[2], interval=None)

    elif call.data == 'unpaid_month':
        start_day = str(date_today.day)
        start_month = date_today.replace(month=(date_today.replace(day=1) - timedelta(days=1)).month).month
        today = str(date_today.day)
        current_month = date_today.month

        # интервал дат для календаря
        interval = {
            # импорт константы из tgbot.services.other_functions.conts
            'start_day': start_day, 'start_month': list_months.get(start_month),
            'end_day': today, 'end_month': list_months.get(current_month),
        }
        response = await settings_for_select_period_unpaid_orders(call, session, str(user[3]), user[2], interval)

    if response.get('status') == 200:
        await call.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_del_unpaid.message_id)

        unpaid_orders = response.get('unpaid_orders')
        if not unpaid_orders:
            await call.message.answer(text=f'{period.get(call.data).capitalize()} неоплаченные заказы отсутствуют ✅')
        else:
            for order in unpaid_orders:
                await call.message.answer(text=f'❌ {period.get(call.data).capitalize()}\n'
                                               f'Номер заказа: {order[0]}\n'
                                               f'Дата начала: {order[1]}\n'
                                               f'Дата завершения: {order[2]}\n'
                                               f'Маршрут: {order[3]}\n\n')
    else:
        await call.message.answer('Ошибка запроса! Попробуйте позже..')
        await call.message.bot.send_message(
            chat_id=admin,
            text=f'Ошибка запроса при получении неоплаченных заказов у {str(user[0])} {str(user[1])},'
                 f' описание: {response}.')

    await state.finish()


async def get_earnings(message: Message, session, state: FSMContext):
    """Генерация клавиатуры для выбора периода по заработку."""
    # telegra_id пользователя
    telegram_id = message.chat.id
    user = await get_user(session, telegram_id)
    if user is not None:
        msg_delete_earn = await message.answer(
            text='Выберите период для отображения заработка', reply_markup=earnings_keyboard)
        await state.update_data(msg_delete_earn=msg_delete_earn.message_id)
    else:
        await message.answer(f'У вас нет доступа!')


async def cancel_unpaid_order(call: CallbackQuery, state: FSMContext):
    """Отмена действий по функции заработка."""
    msg_for_delete = (await state.get_data()).get('msg_delete_unpaid')
    await call.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_for_delete)
    await state.finish()


async def select_period_earnings(call: CallbackQuery, session, state: FSMContext):
    """Выбор периода для получения информации о заработке."""
    admin = call.message.bot.get('config').tg_bot.admin_ids[0]
    telegram_id = call.message.chat.id
    user = await get_user(session, telegram_id)

    # отмена действий по функции заработка
    msg_for_delete = (await state.get_data()).get('msg_delete_earn')
    await call.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_for_delete)

    # сохраняем сегодняшнюю дату
    date_today = date.today()
    response = None
    date_last_month = date_today.replace(month=(date_today.replace(day=1) - timedelta(days=1)).month)
    period = {
        'earnings_today': f'за сегодня: {date_today.strftime("%d.%m.%Y г.")}',
        'earnings_yesterday': f'за вчерашний день: {(date_today - timedelta(days=1)).strftime("%d.%m.%Y г.")}',
        'earnings_week':
            f'за неделю: с {(date_today - timedelta(weeks=1)).strftime("%d.%m.%Y г.")} '
            f'по {date_today.strftime("%d.%m.%Y г.")}',
        'earnings_month':
            f'за месяц: с {date_last_month.strftime("%d.%m.%Y г.")} '
            f'по {date_today.strftime("%d.%m.%Y г.")}'
    }

    msg_del_earn = await call.message.answer(
        text=f'🚀 Загрузка отчета из диспетчерской {period.get(call.data)} Ожидайте..')

    if call.data == 'earnings_today':
        day = str(date_today.day)
        month = date_today.month

        # интервал дат для календаря
        interval = {
            # импорт константы из tgbot.services.other_functions.conts
            'start_day': day, 'start_month': list_months.get(month),
            'end_day': day, 'end_month': list_months.get(month),
        }
        response = await settings_for_select_period_earnings_driver(call, session, str(user[3]), user[2], interval)

    elif call.data == 'earnings_yesterday':
        yesterday = str((date_today - timedelta(days=1)).day)
        month = date_today.month

        # интервал дат для календаря
        interval = {
            # импорт константы из tgbot.services.other_functions.conts
            'start_day': yesterday, 'start_month': list_months.get(month),
            'end_day': yesterday, 'end_month': list_months.get(month),
        }

        response = await settings_for_select_period_earnings_driver(call, session, str(user[3]), user[2], interval)

    elif call.data == 'earnings_week':
        start_day = str((date_today - timedelta(weeks=1)).day)
        start_month = (date_today - timedelta(weeks=1)).month
        today = str(date_today.day)
        current_month = date_today.month

        # интервал дат для календаря
        interval = {
            # импорт константы из tgbot.services.other_functions.conts
            'start_day': start_day, 'start_month': list_months.get(start_month),
            'end_day': today, 'end_month': list_months.get(current_month),
        }
        response = await settings_for_select_period_earnings_driver(call, session, str(user[3]), user[2], interval)

    elif call.data == 'earnings_month':
        start_day = str(date_today.day)
        start_month = date_today.replace(month=(date_today.replace(day=1) - timedelta(days=1)).month).month
        today = str(date_today.day)
        current_month = date_today.month

        # интервал дат для календаря
        interval = {
            # импорт константы из tgbot.services.other_functions.conts
            'start_day': start_day, 'start_month': list_months.get(start_month),
            'end_day': today, 'end_month': list_months.get(current_month),
        }

        response = await settings_for_select_period_earnings_driver(call, session, str(user[3]), user[2], interval)

    if response.get('status') == 200:
        await call.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_del_earn.message_id)

        string = response.get('earnings')
        if len(string) < 16:
            string.insert(12, '0,00')

        await call.message.answer(text=f'📊 <b> Отчет {period.get(call.data)}</b>\n\n'
                                       f'Завершённые поездки: {string[0]}\n'
                                       f'Сумма с таксометра: {string[1]}\n'
                                       f'Пробег с пассажиром: {string[2]}\n\n'
                                       f'Наличные: {string[3]}\n'
                                       f'Оплата по карте: {string[4]}\n'
                                       f'Корпоративная оплата: {string[5]}\n'
                                       f'Чаевые: {string[6]}\n'
                                       f'Промоакции: {string[7]}\n'
                                       f'Бонус: {string[8]}\n'
                                       f'Комиссии платформы: {string[9]}\n'
                                       f'Комиссии партнёра: {string[10]}\n'
                                       f'Прочие платежи платформы: {string[11]}\n'
                                       f'Заправки: {string[12]}\n\n'
                                       f'ИТОГО: {string[13]}\n'
                                       f'Часы работы: {string[14]}\n'
                                       f'Среднечасовой заработок: {string[15]}\n')
    else:
        await call.message.answer('Ошибка запроса! Попробуйте позже..')
        await call.message.bot.send_message(
            chat_id=admin,
            text=f'Ошибка запроса при получении неоплаченных заказов у {user[0]} {user[1]},'
                 f' описание: {response}.')
    await state.finish()


async def cancel_earnings(call: CallbackQuery, state: FSMContext):
    """Отмена действий по функции заработка."""
    msg_for_delete = (await state.get_data()).get('msg_delete_earn')
    await call.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_for_delete)
    await state.finish()


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, CommandStart(), state='*')
    dp.register_message_handler(payment_method, text=['💳Безнал', '💵Нал / Безнал', '🕰Смена в долг'])
    dp.register_message_handler(amount_order, text='🏁Завершить тек. заказ')
    dp.register_callback_query_handler(complete_order, text=order_types)
    dp.register_message_handler(cancel_order, text='❌Отменить текущий заказ')
    dp.register_callback_query_handler(confirm_cancel_order, text=['cancel_confirm', 'not_cancel'])
    dp.register_message_handler(get_help, text='📝Справка')
    dp.register_message_handler(get_unpaid_orders, text='📈Неоплаченные заказы')
    dp.register_callback_query_handler(select_period_unpaid_orders, text=callback_unpaid)
    dp.register_callback_query_handler(cancel_unpaid_order, text='unpaid_cancel')
    dp.register_message_handler(get_earnings, text='💰Заработок')
    dp.register_callback_query_handler(select_period_earnings, text=callback_earnings)
    dp.register_callback_query_handler(cancel_earnings, text='earnings_cancel')
