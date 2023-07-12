import logging

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.models.query import add_url_driver
from tgbot.services.other_functions.phone_formatter import phone_formatting
from tgbot.services.requests.authentication import authentication_requests
from tgbot.services.requests.limit.change_limit import change_limit_requests, change_limit_by_url_driver_requests


# load_dotenv()


async def change_of_payment_method(message, session, limit, phone):  # f1fba85243a74206954e19c5a7151cd0
    """
    Запросы на изменение лимита водителей.
    Обработка запросов в отдельном блокирующем потоке.
    """
    try:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            # вход на страницу водителя по его id
            from tgbot.models.query import get_url_driver_limit
            format_phone = phone_formatting(phone)
            url_driver = await get_url_driver_limit(session, format_phone)

            # если id нет, то выполняется вход с дальнейшей записью id водителя в бд
            status = None
            if url_driver is None:
                status, url = await loop.run_in_executor(pool, change_limit_requests, phone, limit)
                await add_url_driver(session, url, int(phone))

            # если id водителя есть, то сразу получаем доступ к странице водителя
            elif url_driver is not None:
                status = await loop.run_in_executor(
                    pool, change_limit_by_url_driver_requests, limit, url_driver[0])

            if not status and status is not None:
                # отправление сообщения админу для ввода кода
                admin = message.bot.get('config').tg_bot.admin_ids[0]
                await message.bot.send_message(chat_id=admin, text='Ожидайте код для авторизация!')

                # передача состояния администратору для ввода кода и записи в очередь !
                await message.bot.get('dp').storage.set_state(
                    chat=admin, user=admin, state='CodeConfirmState:code')
                queue = message.bot.get('queue')

                # запрос на получение пароля из бд
                from tgbot.models.query import get_account_password
                password = await get_account_password(session)

                # прямой запрос на авторизацию
                auth = await loop.run_in_executor(pool, authentication_requests, queue, password)
                if auth:
                    status = await loop.run_in_executor(pool, change_limit_requests, phone, limit)
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
