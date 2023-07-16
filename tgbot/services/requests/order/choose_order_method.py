import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.keyboards.inline_users import order_processing
from tgbot.models.query import add_url_driver
from tgbot.services.other_functions.phone_formatter import phone_formatting
from tgbot.services.requests.authentication import authentication_requests, send_code_bot
from tgbot.services.requests.order.work_with_order import working_order_requests

from aiogram.types import Message


async def change_working_order_method(obj, session, state, phone, way, amount):
    """
    Работа запросов по завершению заказов у водителей.
    Обработка запросов в отдельном потоке.
    """
    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            # вход на страницу водителя по его id
            from tgbot.models.query import get_url_driver_limit
            format_phone = phone_formatting(phone)
            url_driver = await get_url_driver_limit(session, format_phone)
            # если id нет, то выполняется вход с дальнейшей записью id водителя в бд,
            # ссылка на заказ для дальнейшего завершения
            if url_driver is None:
                request = await loop.run_in_executor(
                        pool, working_order_requests, phone, way, amount)

                if request.get('status') != 401:
                    await add_url_driver(session, request.get('url_driver'), int(phone))
                    await complete_or_empty_order(obj, way, state, request)
                    return request
                else:
                    logging.error(
                        'Возникла ошибка связанная скорее всего с отсутствием элемента на странице',
                        request.get('status')
                    )

            # если id водителя есть, то сразу получаем доступ к странице водителя
            elif url_driver is not None:
                request = await loop.run_in_executor(
                        pool, working_order_requests, phone, way, amount, url_driver[0])

                if request.get('status') != 401:
                    await complete_or_empty_order(obj, way, state, request)
                    return request
                else:
                    logging.error(
                        'Возникла ошибка связанная скорее всего с отсутствием элемента на странице',
                        request.get('status')
                    )

            if request.get('status') == 401:
                # получение кода для авторизации
                password, queue = await send_code_bot(obj, session)
                # прямой запрос на авторизацию
                auth = await loop.run_in_executor(pool, authentication_requests, queue, password)
                if auth:
                    request = await loop.run_in_executor(
                        pool, working_order_requests, phone, way, amount)

                    if request.get('status') != 401:
                        await complete_or_empty_order(obj, way, state, request)
                        return request
                else:
                    return 'Авторизации не выполнена! Попробуйте позже..'

    except TimeoutError as e:
        logging.error(f'Возникла ошибка времени ожидания: {e}')
        return 'Возникла ошибка времени ожидания'
    except aiohttp.ClientError as e:
        logging.error(f'Возникла сетевая ошибка: {e}')
        return 'Сетевая ошибка'
    except Exception as e:
        logging.error(f'Ошибка {e}')
        logging.exception('Ошибка в обработке команды: %s', e)
        return 'Ошибка на стороне сервера телеграм'


async def complete_or_empty_order(obj, way, state, request):
    """Работа с пустыми и непустыми заказами."""
    msg_for_delete_current_order = (await state.get_data()).get('msg_for_delete_current_order')
    if msg_for_delete_current_order is not None:
        if isinstance(obj, Message):
            await obj.bot.delete_message(chat_id=obj.chat.id,
                                         message_id=msg_for_delete_current_order)
        else:
            await obj.bot.delete_message(chat_id=obj.message.chat.id,
                                         message_id=msg_for_delete_current_order)
    if request.get('empty_order') is not None:
        if isinstance(obj, Message):
            await obj.answer(request.get('empty_order'))
        else:
            await obj.message.answer(request.get('empty_order'))

    elif request.get('empty_order') is None:
        await amount_order(
            obj, way, state,
            request.get('number_order'),
            request.get('description'),
            request.get('address'),
            request.get('price')
        )


async def amount_order(obj, way, state, number_order, description, address, price):
    """Ввод клавиатуры с кнопками и суммой заказа по фикс. цене / таксометру."""
    if way == 'amount':
        if isinstance(obj, Message):
            msg_order_delete = await obj.answer(
                text=f'{number_order}\n'
                     f'Тариф {description[0]}\n'
                     f'Тип оплаты {description[1]}\n'
                     f'Адрес заказа {address}',
                reply_markup=order_processing(price)
            )
            await state.update_data(msg_order_delete=msg_order_delete.message_id)
            await obj.delete()

        else:
            msg_order_delete = await obj.message.answer(
                text=f'{number_order}\n'
                     f'Тариф {description[0]}\n'
                     f'Тип оплаты {description[1]}\n'
                     f'Адрес заказа {address}',
                reply_markup=order_processing(price)
            )
            await state.update_data(msg_order_delete=msg_order_delete.message_id)
            await obj.message.delete()
