from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from aiogram.bot import Bot


commands = [
    '/remove_user',
    '/users',
    '/edit_user',
    '/newsend',
    '/change_password',
    '/configure_help'
]


async def set_default_commands(bot: Bot, user_id):
    """Команды для админа."""

    if user_id in bot.get('config').tg_bot.admin_ids:
        await bot.set_my_commands(
            commands=[
                BotCommand('remove_user', 'Удалить водителя из базы'),
                BotCommand('users', 'Список водителей'),
                BotCommand('edit_user', 'Редактировать водителя'),
                BotCommand('newsend', 'Рассылка писем'),
                BotCommand('change_password', 'Изменить пароль'),
                BotCommand('configure_help', 'Справка')
            ],
            scope=BotCommandScopeChat(user_id)
        )
    else:
        # команды для всех
        await bot.set_my_commands(
            commands=[
                BotCommand('start', 'Запуск работы со службой такси'),
            ],
            scope=BotCommandScopeAllPrivateChats()
        )
