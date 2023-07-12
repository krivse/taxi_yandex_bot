import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.keyboards.inline_users import order_processing
from tgbot.models.query import add_url_driver
from tgbot.services.other_functions.phone_formatter import phone_formatting
from tgbot.services.requests.authentication import authentication_requests

# working_order_by_url_driver_requests

from aiogram.types import Message

from tgbot.services.requests.unpaid_orders.unpaid_orders import unpaid_orders_requests


# load_dotenv()


async def settings_for_select_period_unpaid_orders(obj, session, phone, interval):
    """
    Работа запросов по выдаче информации о неоплаченных заказах.
    Обработка запросов в отдельном потоке.
    """
    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            # вход на страницу водителя по его id
            from tgbot.models.query import get_url_driver_limit
            format_phone = phone_formatting(str(phone))
            url_driver_order = await get_url_driver_limit(session, format_phone)

            # если id нет, то выполняется вход с дальнейшей записью id водителя в бд,
            # ссылка на заказ для дальнейшего завершения
            status = None
            if url_driver_order is None:
                status, url_driver_order, unpaid_o = await loop.run_in_executor(
                    pool, unpaid_orders_requests, phone, interval
                )
                await add_url_driver(session, url_driver_order, int(phone))

            elif url_driver_order is not None:
                status, url_driver_order, unpaid_o = await loop.run_in_executor(
                    pool, unpaid_orders_requests, phone, interval, url_driver_order[0])

            if not status and status is not None:
                # отправление сообщения админу для ввода кода
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
                    status, url_driver_order, unpaid_o = await loop.run_in_executor(
                        pool, unpaid_orders_requests, phone, interval)
                    await add_url_driver(session, url_driver_order, int(phone))
                else:
                    return 'Авторизации не выполнена! Попробуйте позже..'

            if status == 200:
                return status, unpaid_o
            else:
                return 400, unpaid_o
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
