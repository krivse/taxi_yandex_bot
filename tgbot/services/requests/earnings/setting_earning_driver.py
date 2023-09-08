import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.services.requests.authentication import authentication_requests, send_code_bot
from tgbot.services.requests.earnings.eranings_driver import earnings_driver_requests


async def settings_for_select_period_earnings_driver(obj, session, phone, taxi_id, interval):
    """
    Работа запросов по выдаче информации о заработке водителя.
    Обработка запросов в отдельном потоке.
    """
    request = {}
    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            # вход на страницу водителя по его id
            request = await loop.run_in_executor(
                pool, earnings_driver_requests, phone, interval, taxi_id)

            if request.get('status') != 401:
                return request
            elif request.get('status') == 401:
                # получение кода для авторизации
                password, queue = await send_code_bot(obj, session)
                # прямой запрос на авторизацию
                auth = await loop.run_in_executor(pool, authentication_requests, queue, password)
                if auth.get('status') == 201:
                    request = await loop.run_in_executor(
                        pool, earnings_driver_requests, phone, interval)
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
