import re
import json
import logging
# from dotenv import load_dotenv

import aiohttp
import asyncio
from asyncio.exceptions import TimeoutError
from concurrent.futures import ThreadPoolExecutor

from tgbot.services.requests_txya import authentication, taxi_ya_park

# load_dotenv()


async def change_of_payment_method(message, session, limit, taxi_id, header):  # f1fba85243a74206954e19c5a7151cd0
    async with aiohttp.ClientSession() as connect:
        url = f'https://fleet-api.taxi.yandex.net/v2/parks/contractors/driver-profile?contractor_profile_id={taxi_id}'
        headers = {
            'X-Client-ID': header.X_Client_ID,  # os.getenv('X_Client_ID')
            'X-API-Key': header.X_API_Key,  # os.getenv('X_API_Key')
            'X-Park-ID': header.X_Park_ID  # os.getenv('X_Park_ID')
        }

        try:
            response = await (await connect.get(url.format(), headers=headers)).json()

            # получение данных из профиля для выполнения корректного запроса PUT.
            account = response.get('account')
            person = response.get('person')
            profile = response.get('profile')
            order_provider = response.get('order_provider')
            car_id = response.get('car_id')

            params = {
                'account': {
                    'balance_limit': limit,
                    'work_rule_id': account.get('work_rule_id'),
                    'payment_service_id': account.get('payment_service_id'),
                    'block_orders_on_balance_below_limit': account.get('block_orders_on_balance_below_limit')
                },
                'person': {
                    'full_name': {
                        'first_name': person.get('full_name').get('first_name'),
                        'middle_name': person.get('full_name').get('middle_name'),
                        'last_name': person.get('full_name').get('last_name')},
                    'contact_info': {
                        'phone': person.get('contact_info').get('phone')},
                    'driver_license': {
                        'country': person.get('driver_license').get('country'),
                        'expiry_date': person.get('driver_license').get('expiry_date'),
                        'issue_date': person.get('driver_license').get('issue_date'),
                        'number': person.get('driver_license').get('number')},
                    'driver_license_experience': {
                        'total_since_date': person.get('driver_license_experience').get('total_since_date')}
                },
                'profile': {
                    'hire_date': profile.get('hire_date'),
                    'work_status': profile.get('work_status')
                },
                'order_provider': {
                    'platform': order_provider.get('platform'),
                    'partner': order_provider.get('partner')
                },
                'car_id': car_id,
            }

            # запрос на редакитрование лимита в профиле.
            response_put = await connect.put(url.format(),
                                             headers=headers,
                                             data=json.dumps(params))

            if response_put is not None and response_put.status == 400:
                loop = asyncio.get_running_loop()
                phone = response.get('person').get('contact_info').get('phone')

                with ThreadPoolExecutor() as pool:
                    status = await loop.run_in_executor(pool, taxi_ya_park, phone, limit)

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

                        # прямой запрос на аторизацию
                        auth = await loop.run_in_executor(pool, authentication, queue, password)
                        if auth:
                            status = await loop.run_in_executor(pool, taxi_ya_park, phone, limit)
                        else:
                            return 'Авторизации не выполнена! Попробуйте позже..'
                return status
            elif response_put is not None and response_put.status == 200:
                return response_put.status
            else:
                return response_put

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


async def get_driver_profile(phone, header):
    async with aiohttp.ClientSession() as connect:
        url = 'https://fleet-api.taxi.yandex.net/v1/parks/driver-profiles/list'
        query = {"query": {"park": {"id": header.X_Park_ID}}}
        headers = {'X-Client-ID': header.X_Client_ID,
                   'X-API-Key':  header.X_API_Key}

        try:
            # форматирование телефона.
            user_phone = phone_formatting(phone)

            # получение списка профилей.
            response = await (await connect.post(url, json=query, headers=headers)).json()
            user = None

            # перебор профилей и запись необоздимых данных из профиля.
            for profile in range(len(response.get('driver_profiles'))):
                driver_phone = int(response.get('driver_profiles')[profile].get('driver_profile').get('phones')[0])
                if user_phone == driver_phone:
                    first_name = response.get('driver_profiles')[profile].get('driver_profile').get('first_name')
                    last_name = response.get('driver_profiles')[profile].get('driver_profile').get('last_name')
                    middle_name = response.get('driver_profiles')[profile].get('driver_profile').get('middle_name', '-')
                    id_user_taxi = response.get('driver_profiles')[profile].get('driver_profile').get('id')
                    user = first_name, last_name, middle_name, user_phone, id_user_taxi
                    return user
            if not user:
                return f'Телефонный номер - {phone} - не найден!\n' \
                       f'Проверьте, что номер был введен корректно и попробуйте снова.\n' \
                       f'Попробуйте ввести в формате 79997775533'
        except TimeoutError as e:
            logging.error(f'Возникла ошибка времени ожидания: {e}')
        except aiohttp.ClientError as e:
            logging.error(f'Возникла сетевая ошибка: {e}')
        except Exception as e:
            logging.error(f'Ошибка {e}')


def phone_formatting(user_phone):
    """Форматирование телеофона 79999999999."""
    return int(re.sub(r'[+() -]', '', user_phone).replace(user_phone[0], '7', 1))
