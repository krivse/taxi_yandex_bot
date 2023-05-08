from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher import FSMContext

from tgbot.keyboards.user_button import choose_menu_for_user
from tgbot.misc.states import RegisterState
from tgbot.models.query import access_debt_mode, get_user
from tgbot.services.api_txya import change_of_payment_method
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
        await state.update_data(first_name=user[0], middle_name=user[1], taxi_id=user[2])


async def payment_method(message: Message, session, state: FSMContext):
    """Выбор способа оплаты."""
    admin = message.bot.get('config').tg_bot.admin_ids[0]
    # ключи для выполнения запрос к API Yandex
    header = message.bot.get('config').misc
    # название кнопки
    method = message.text
    # реакция на команду /start иx получение состояиния юзера
    user = await state.get_data()
    first_name, middle_name, taxi_id = user.get('first_name'), user.get('middle_name'), user.get('taxi_id')
    # telegra_id пользователя
    telegram_id = message.from_user.id

    # если пользователь нажал не на команду, а сразу на кнопку, то будет запрос к БД.
    if user == {}:
        user = await get_user(session, telegram_id)
        if user is not None:
            first_name, middle_name, taxi_id = user
    if method == 'Безнал' and user is not None:
        # установка лимита для оплаты по безналу.
        response = await change_of_payment_method(message, session, '15000', taxi_id, header)
        if response == 200:
            await message.answer(f'{first_name} {middle_name}, '
                                 'Вам установлен лимит 15000 руб. '
                                 'Пока Ваш баланс ниже этой суммы, вам будут поступаь только БЕЗНАЛИЧНЫЕ заказы.')
        else:
            await message.answer('Ошибка запроса! Попробуйте позже..')
            await message.bot.send_message(
                chat_id=admin,
                text=f'Ошибка запроса при изменения лимита у {first_name} {middle_name}, ошибка: {response}')
    elif method == 'Нал / Безнал' and user is not None:
        # установка лимита для оплаты по нал / безннал.
        response = await change_of_payment_method(message, session, '50', taxi_id, header)
        if response == 200:
            await message.answer(f'{first_name} {middle_name}, '
                                 'Вам установлен лимит 50 руб. '
                                 'Теперь Вам будут поступать НАЛИЧНЫЕ и БЕЗНАЛИЧНЫЕ заказы.')
        else:
            await message.answer('Ошибка запроса! Попробуйте позже..')
            await message.bot.send_message(
                chat_id=664005061, #admin,
                text=f'Ошибка запроса при изменения лимита у {first_name} {middle_name}, ошибка: {response}.')
    elif method == 'Смена в долг' and user is not None:
        # установка лимита для режима работы в долг.
        access, limit = await access_debt_mode(session, telegram_id)
        if access:
            response = await change_of_payment_method(message, session, str(limit), taxi_id, header)
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


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, CommandStart(), state='*')
    dp.register_message_handler(payment_method, text=['Безнал', 'Нал / Безнал', 'Смена в долг'])
