from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.handler import current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled
from aiogram.dispatcher.handler import CancelHandler


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=3600, key_prefix='antiflood_'):
        self.limit = limit
        self.prefix = key_prefix
        # инициализируем базовый класс BasMiddleware.
        super().__init__()

    async def throtlle(self, message: types.Message):  # тротлинг для types.Message
        # Получить текущий хендлер
        handler = current_handler.get()
        if not handler:
            return
        # забираем атрибут и возвращает limit.
        limit = getattr(handler, 'throttling_rate_limit', self.limit)
        # возвращаем antiflood_bot_start.
        key = getattr(handler, 'throttling_key', f'{self.prefix}_{handler.__name__}')

        # получить текущий диспатчер.
        dp = Dispatcher.get_current()
        try:
            # если троттл сработал.
            await dp.throttle(key, rate=limit)
        except Throttled as e:
            # обновляем лимит
            self.limit = e.rate - e.delta
            await self.target_throttled(message, e)

    @staticmethod
    async def target_throttled(target: types.Message, throttled: Throttled):
        # рассчитывается время после последнего тротлинга.
        # throttled.
        delta = int((throttled.rate - throttled.delta) / 60)
        # проверяем сколько раз нажали на кнопку
        if throttled.exceeded_count > 5:
            await target.answer(f'Вы сможете отправить следующее сообщение через {delta} минут.')
            raise CancelHandler()

    async def on_process_message(self, message, data):
        await self.throtlle(message)
