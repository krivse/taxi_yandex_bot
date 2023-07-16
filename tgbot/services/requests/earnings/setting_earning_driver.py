import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.models.query import add_url_driver
from tgbot.services.other_functions.phone_formatter import phone_formatting
from tgbot.services.requests.authentication import authentication_requests, send_code_bot
from tgbot.services.requests.earnings.eranings_driver import earnings_driver_requests


# load_dotenv()

async def settings_for_select_period_earnings_driver(obj, session, phone, interval):
    """
    Работа запросов по выдаче информации о заработке водителя.
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
            if url_driver_order is None:
                request = await loop.run_in_executor(
                    pool, earnings_driver_requests, phone, interval
                )
                if request.get('status') != 401:
                    await add_url_driver(session, request.get('url_driver'), int(phone))
                    return request

            elif url_driver_order is not None:
                request = await loop.run_in_executor(
                    pool, earnings_driver_requests, phone, interval, url_driver_order[0])
                if request.get('status') != 401:
                    return request

            if request.get('status') == 401:
                # получение кода для авторизации
                password, queue = await send_code_bot(obj, session)
                # прямой запрос на авторизацию
                auth = await loop.run_in_executor(pool, authentication_requests, queue, password)
                if auth:
                    request = await loop.run_in_executor(
                        pool, earnings_driver_requests, phone, interval)
                    if request.get('status') != 401:
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
