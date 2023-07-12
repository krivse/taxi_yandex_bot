import asyncio
import json
import logging
import os
import time
from dotenv import load_dotenv

import aiohttp
from datetime import datetime, timedelta

load_dotenv()


async def get_unpaid_orders(interval):  # header):
    async with aiohttp.ClientSession() as session:
        url = 'https://fleet-api.taxi.yandex.net/v1/parks/orders/list'
        headers = {
            'X-Client-ID': 'taxi/park/bb83932233b3484089a65d301e6aea08',
            # os.getenv('X_Client_ID'),  # header.X_Client_ID,
            'X-API-Key': os.getenv('X_API_Key')  # header.X_API_Key,
        }
        # str(date.isoformat('T', 'seconds'))
        start_date = datetime.now() - timedelta(days=interval)
        now_date = datetime.now()
        params = {
            "limit": 500,
            "query": {
                "park": {
                    "id": os.getenv('X_Park_ID'),
                    "driver_profile": {
                        "id": "1e7da6beb16d4b71b3096d3f8e24409f"
                    },
                    "order": {
                        "booked_at": {
                            "from": str(start_date.isoformat('T', 'seconds')) + "+00:00",
                            "to": str(now_date.isoformat('T', 'seconds') + "+00:00")
                        },
                        "payment_methods": [
                            "card",
                            "cashless",
                            "corp"
                        ],
                        "price": {
                            "from": "0.00",
                            "to": "254.00",
                        },
                        "statuses": [
                            "complete"
                        ]
                    }
                }
            }
        }

        try:
            response = await (await session.post(url, headers=headers, data=json.dumps(params))).text()
            print(response)
        except TimeoutError as e:
            logging.error(f'Возникла ошибка времени ожидания: {e}')
        except aiohttp.ClientError as e:
            logging.error(f'Возникла сетевая ошибка: {e}')
        except Exception as e:
            logging.error(f'Ошибка {e}')

# asyncio.run(get_unpaid_orders(2))
