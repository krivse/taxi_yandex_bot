from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher import FSMContext

from tgbot.keyboards.user_button import menu
from tgbot.misc.states import RegisterState
from tgbot.models.query import get_user
from tgbot.services.api_requests import change_of_payment_method
from tgbot.services.set_commands import set_default_commands


async def user_start(message: Message, session, state: FSMContext):
    """Реакция на команду /start и получение пользователя из БД."""
    user = await get_user(session, message.from_user.id)
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
    else:
        # выводится сообщение об выборе тарифа работы.
        await message.answer(f'{user[0]} {user[1]}, способ оплаты за заказы в Яндекс Про', reply_markup=menu)
        await state.update_data(first_name=user[0], last_name=user[1], taxi_id=user[2])


async def payment_method(message: Message, session, state: FSMContext):
    """Выбор способа оплаты."""
    # ключи для выполнения запрос к API Yandex
    header = message.bot.get('config').misc
    # название кнопки
    method = message.text
    # реакция на команду /start иx получение состояиния юзера
    user = await state.get_data()
    first_name, last_name, taxi_id = user.get('first_name'), user.get('last_name'), user.get('taxi_id')

    # если пользователь нажал не на команду, а сразу на кнопку, то будет запрос к БД.
    if user == {}:
        user = await get_user(session, message.from_user.id)
        if user is not None:
            first_name, last_name, taxi_id = user
    if method == 'Безнал' and user is not None:
        # установка лимита для оплаты по безналу.
        await change_of_payment_method('15000', taxi_id, header)
        await message.answer(f'{first_name} {last_name}, '
                             'ваш лимит 15000 руб. Пока ваш баланс ниже этой '
                             'суммы вам будут поступать только БЕЗНАЛИЧНЫЕ заказы.')
    elif method == 'Нал / Безнал' and user is not None:
        # установка лимита для оплаты по нал / безннал.
        await change_of_payment_method('50', taxi_id, header)
        await message.answer(f'{first_name} {last_name}, ваш лимит 50 руб. '
                             'Теперь вам будут поступать НАЛИЧНЫЕ и БЕЗНАЛИЧНЫЕ заказы.')
    else:
        await message.answer(f'У вас нет доступа!')
    # сбрасывается состояние пользователя.
    await state.finish()


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, CommandStart(), state='*')
    dp.register_message_handler(payment_method, text=['Безнал', 'Нал / Безнал'])
