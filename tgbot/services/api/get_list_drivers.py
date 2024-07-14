import logging
from dotenv import load_dotenv

import aiohttp
from asyncio.exceptions import TimeoutError

from tgbot.services.other_functions.phone_formatter import phone_formatting


load_dotenv()


async def get_driver_profile(phone, header):
    async with aiohttp.ClientSession() as connect:
        url = 'https://fleet-api.taxi.yandex.net/v1/parks/driver-profiles/list'
        query = {"query": {"park": {"id": header.X_Park_ID}}}
        headers = {'X-Client-ID': header.X_Client_ID,
                   'X-API-Key':  header.X_API_Key}
        # query = {"query": {"park": {"id": os.getenv('X_Park_ID')}}}
        # headers = {'X-Client-ID': os.getenv('X_Client_ID'),
        #            'X-API-Key': os.getenv('X_API_Key')}
        try:
            # форматирование телефона.
            user_phone = phone_formatting(phone)

            # получение списка профилей.
            response = await (await connect.post(url, json=query, headers=headers)).json()
            user = None

            # перебор профилей и запись необоздимых данных из профиля.
            for profile in range(len(response.get('driver_profiles'))):
                try:
                    driver_phone = int(response.get('driver_profiles')[profile].get('driver_profile').get('phones')[0])
                except IndexError:
                    driver_phone = 0
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
