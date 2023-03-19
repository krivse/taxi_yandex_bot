from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware


class DatabaseMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    def __init__(self, session):
        super().__init__()
        self.session = session

    async def pre_process(self, obj, data, *args):
        session = self.session()

        data['session'] = session

    async def post_process(self, obj, data, *args):
        session = data['session']
        await session.close()
