import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.models.query import add_url_driver
from tgbot.services.other_functions.phone_formatter import phone_formatting
from tgbot.services.requests.authentication import authentication_requests, send_code_bot
from tgbot.services.requests.limit.change_limit import change_limit_requests


# load_dotenv()


async def change_of_payment_method(obj, session, limit, phone, taxi_id):
    """
    Запросы на изменение лимита водителей.
    Обработка запросов в отдельном блокирующем потоке.
    """
    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            # если id водителя есть, то сразу получаем доступ к странице водителя
            request = await loop.run_in_executor(
                pool, change_limit_requests, phone, limit, taxi_id)
            if request.get('status') != 401:
                return request.get('status')

            if request.get('status') == 401:
                # получение кода для авторизации
                password, queue = await send_code_bot(obj, session)
                # прямой запрос на авторизацию
                auth = await loop.run_in_executor(pool, authentication_requests, queue, password)
                if auth:
                    request = await loop.run_in_executor(pool, change_limit_requests, phone, limit)
                    if request.get('status') != 401:
                        return request.get('status')
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
