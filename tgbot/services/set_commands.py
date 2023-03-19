from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from aiogram.bot import Bot


async def set_default_commands(bot: Bot, user_id):
    """Команды для админа ."""

    if user_id in bot.get('config').tg_bot.admin_ids:
        await bot.set_my_commands(
            commands=[
                BotCommand('remove_user', 'Удалить водителя из базы'),
            ],
            scope=BotCommandScopeChat(user_id)
        )
    else:
        await bot.set_my_commands(
            commands=[
                BotCommand('start', 'Запуск работы со службой такси'),
            ],
            scope=BotCommandScopeAllPrivateChats()
        )
