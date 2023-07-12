import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.keyboards.inline_users import order_processing
from tgbot.models.query import add_url_driver
from tgbot.services.other_functions.phone_formatter import phone_formatting
from tgbot.services.requests.authentication import authentication_requests
from tgbot.services.requests.order.work_with_order import working_order_requests

from aiogram.types import Message
# load_dotenv()


async def change_working_order_method(obj, session, state, phone, way, amount):  # f1fba85243a74206954e19c5a7151cd0
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
            url_driver_order = await get_url_driver_limit(session, format_phone)
            # если id нет, то выполняется вход с дальнейшей записью id водителя в бд,
            # ссылка на заказ для дальнейшего завершения
            status = None
            msg_for_delete_current_order = (await state.get_data()).get('msg_for_delete_current_order')
            if url_driver_order is None:
                status, url_driver_order, amount, number_order,\
                    description, address, empty_order = await loop.run_in_executor(
                        pool, working_order_requests, phone, way, amount)
                await add_url_driver(session, url_driver_order, int(phone))

                if empty_order is not None:
                    if isinstance(obj, Message):
                        await obj.answer(empty_order)
                    else:
                        await obj.message.answer(empty_order)
                elif empty_order is None:
                    await amount_order(obj, way, state, number_order, description, address, amount)

                await obj.bot.delete_message(chat_id=obj.chat.id, message_id=msg_for_delete_current_order)

            # если id водителя есть, то сразу получаем доступ к странице водителя
            elif url_driver_order is not None:
                status, url_driver_order, amount, number_order, \
                    description, address, empty_order = await loop.run_in_executor(
                        pool, working_order_requests, phone, way, amount, url_driver_order[0])

                if empty_order is not None:
                    if isinstance(obj, Message):
                        await obj.answer(empty_order)
                    else:
                        await obj.message.answer(empty_order)
                elif empty_order is None:
                    await amount_order(obj, way, state, number_order, description, address, amount)
                await obj.bot.delete_message(chat_id=obj.chat.id, message_id=msg_for_delete_current_order)

            if not status and status is not None:
                # отправление сообщения админу для ввода кода
                if isinstance(obj, Message):
                    admin = obj.bot.get('config').tg_bot.admin_ids[0]
                    await obj.bot.send_message(chat_id=admin, text='Ожидайте код для авторизация!')

                    # передача состояния администратору для ввода кода и записи в очередь !
                    await obj.bot.get('dp').storage.set_state(
                        chat=admin, user=admin, state='CodeConfirmState:code')
                    queue = obj.bot.get('queue')
                else:
                    admin = obj.message.bot.get('config').tg_bot.admin_ids[0]
                    await obj.message.bot.send_message(chat_id=admin, text='Ожидайте код для авторизация!')

                    # передача состояния администратору для ввода кода и записи в очередь !
                    await obj.message.bot.get('dp').storage.set_state(
                        chat=admin, user=admin, state='CodeConfirmState:code')
                    queue = obj.bot.get('queue')
                # запрос на получение пароля из бд
                from tgbot.models.query import get_account_password
                password = await get_account_password(session)

                # прямой запрос на авторизацию
                auth = await loop.run_in_executor(pool, authentication_requests, queue, password)
                if auth:
                    status, url_driver_order = await loop.run_in_executor(
                        pool, working_order_requests, phone, way, amount)
                    await add_url_driver(session, url_driver_order, int(phone))
                else:
                    return 'Авторизации не выполнена! Попробуйте позже..'

            return status
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


async def amount_order(obj, way, state, number_order, description, address, amount):
    """Ввод клавиатуры с кнопками и суммой заказа по фикс. цене / таксометру."""
    if way == 'amount':
        if isinstance(obj, Message):
            msg_order_delete = await obj.answer(
                text=f'{number_order}\n'
                     f'Тариф {description[0]}\n'
                     f'Тип оплаты {description[1]}\n'
                     f'Адрес заказа {address}',
                reply_markup=order_processing(amount)
            )
            await state.update_data(msg_order_delete=msg_order_delete.message_id)
            await asyncio.sleep(10)
            await obj.delete()

        else:
            msg_order_delete = await obj.message.answer(
                text=f'{number_order}\n'
                     f'Тариф {description[0]}\n'
                     f'Тип оплаты {description[1]}\n'
                     f'Адрес заказа {address}',
                reply_markup=order_processing(amount)
            )
            await state.update_data(msg_order_delete=msg_order_delete.message_id)
            await asyncio.sleep(10)
            await obj.message.delete()
