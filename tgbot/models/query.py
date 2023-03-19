from sqlalchemy import delete, insert, select

from tgbot.models.models import User
from tgbot.services.api_requests import phone_formatting


async def get_user(session, user_id):
    result = (await session.execute(select(
        User.first_name, User.middle_name, User.taxi_id
    ).where(User.telegram_id == user_id))).fetchone()

    return result


async def add_user(session, user):
    """Запрос на добавление в БД."""
    await session.execute(insert(User).values(
        telegram_id=user.get('telegram_id'),
        first_name=user.get('first_name'),
        last_name=user.get('last_name'),
        middle_name=user.get('middle_name', '-'),
        phone=user.get('phone'),
        taxi_id=user.get('taxi_id'))
    )
    await session.commit()


async def drop_user(session, phone, state):
    """Запрос на удаление из БД."""
    # проверка номер телеофна на соответствие.
    user_phone = phone_formatting(phone)
    # проверяем есть ли такой пользователь
    user = (await session.execute(select(User.telegram_id).where(User.phone == user_phone))).first()

    if user is not None:
        # удаление номера телефона
        await session.execute(delete(User).where(User.phone == user_phone))
        await session.commit()
        # сброс состояния пользователя.
        await state.finish()
        return f'Пользователь с номером телефона +{user_phone} успешно удален'
    else:
        return f'Пользователь с номером телефона +{user_phone} не найден. Попробуйте ввести ещё раз..'
