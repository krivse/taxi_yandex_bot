import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.services.requests.authentication import authentication_requests, send_code_bot
from tgbot.services.requests.limit.change_limit import change_limit_requests


async def change_of_payment_method(obj, session, limit, phone, taxi_id):
    """
    Запросы на изменение лимита водителей.
    Обработка запросов в отдельном блокирующем потоке.
    """
    request = {}
    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            # если id водителя есть, то сразу получаем доступ к странице водителя
            request = await loop.run_in_executor(
                pool, change_limit_requests, phone, limit, taxi_id)

            if request.get('status') != 401:
                return request
            elif request.get('status') == 401:
                # получение кода для авторизации
                password, queue = await send_code_bot(obj, session)
                # прямой запрос на авторизацию
                auth = await loop.run_in_executor(pool, authentication_requests, queue, password)
                if auth.get('status') == 201:
                    request = await loop.run_in_executor(pool, change_limit_requests, phone, limit)
                    if request.get('status') != 401:
                        return request
                    elif request.get('status') == 401:
                        request['status'] = 401
                        request['message'] = 'Авторизации не выполнена! Попробуйте позже..'
                        return request
                else:
                    request['status'] = 401
                    request['message'] = 'Авторизации не выполнена! Попробуйте позже..'
                    return request

    except TimeoutError as e:
        logging.error(f'Возникла ошибка времени ожидания: {e}')
        request['status'] = 400
        request['message'] = 'Возникла ошибка времени ожидания'
        return request
    except aiohttp.ClientError as e:
        logging.error(f'Возникла сетевая ошибка: {e}')
        request['status'] = 400
        request['message'] = f'Возникла сетевая ошибка'
        return request
    except Exception as e:
        logging.error(f'Ошибка {e}')
        logging.exception('Ошибка в обработке команды: %s', e)
        request['status'] = 400
        request['message'] = f'Ошибка на стороне сервера'
        return request
