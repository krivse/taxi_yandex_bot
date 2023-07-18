import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.models.query import add_url_driver
from tgbot.services.other_functions.phone_formatter import phone_formatting
from tgbot.services.requests.authentication import authentication_requests, send_code_bot
from tgbot.services.requests.unpaid_orders.unpaid_orders import unpaid_orders_requests


# load_dotenv()


async def settings_for_select_period_unpaid_orders(obj, session, phone, taxi_id, interval):
    """
    Работа запросов по выдаче информации о неоплаченных заказах.
    Обработка запросов в отдельном потоке.
    """
    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            # вход на страницу водителя по его id
            request = await loop.run_in_executor(
                    pool, unpaid_orders_requests, phone, interval, taxi_id)
            if request.get('status') != 401:
                return request

            if request.get('status') == 401:
                # получение кода для авторизации
                password, queue = await send_code_bot(obj, session)
                # прямой запрос на авторизацию
                auth = await loop.run_in_executor(pool, authentication_requests, queue, password)
                if auth:
                    request = await loop.run_in_executor(
                        pool, unpaid_orders_requests, phone, interval)

                    if request.get('status') != 401:
                        return request
                else:
                    return 'Авторизации не выполнена! Попробуйте позже..'

    except TimeoutError as e:
        logging.error(f'Возникла ошибка времени ожидания: {e}')
        return f'Возникла ошибка времени ожидания: {e}'
    except aiohttp.ClientError as e:
        logging.error(f'Возникла сетевая ошибка: {e}')
        return 'Сетевая ошибка'
    except Exception as e:
        logging.error(f'Ошибка {e}')
        logging.exception('Ошибка в обработке команды: %s', e)
        return f'описание ошибки: {e}'
