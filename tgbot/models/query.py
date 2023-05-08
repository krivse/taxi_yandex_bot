from sqlalchemy import delete, insert, select, update

from tgbot.models.models import User, DriverSettings, AccountPark
from tgbot.services.api_txya import phone_formatting


async def update_account_password(session, password):
    """Обновление / установка пароля парка."""
    exists = await get_account_password(session)

    if exists is None:
        result = (await session.execute(
            insert(
                AccountPark
            ).values(
                password=password
            ).returning(AccountPark.password))).scalar()
    if exists is not None:
        result = (await session.execute(
            update(
                AccountPark
            ).where(
                AccountPark.id == 1
            ).values(
                password=password
            ).returning(AccountPark.password))).scalar()

    await session.commit()
    return result


async def get_account_password(session):
    """Получение пароля парка."""
    result = (await session.get(
        AccountPark, 1))

    if result is None:
        return result
    elif result is not None:
        return result.password


async def delete_access_user(session, telegram_id):
    """Отключить доступ пользователю для смены в долг."""
    result = (await session.execute(
        update(
            DriverSettings
        ).where(
            DriverSettings.telegram_id == telegram_id
        ).values(
            access_limit=False).returning(DriverSettings.access_limit))).scalar()
    await session.commit()

    return result


async def add_or_update_limit_user(session, taxi_id, limit):
    """Добавление или обновление записи водителя с лимитом."""

    # возращается две записи из бд, если в обоих таблицах есть связаная запись.
    user = (await session.execute(
        select(
            DriverSettings.telegram_id, User.first_name, User.middle_name
        ).join(
            User
        ).where(
            User.taxi_id == taxi_id
        ).union_all(
            select(
                User.telegram_id, User.first_name, User.middle_name
            ).where(
                User.taxi_id == taxi_id)

        ))).fetchall()

    # если записи нет в driver_settings, то она создается
    if len(user) == 1:
        await session.execute(
            insert(
                DriverSettings
            ).values(
                telegram_id=user[0][0],
                limit=limit,
                access_limit=True
            ))
    # если такая запись есть, то она обновляется
    elif len(user) > 1:
        await session.execute(
            update(
                DriverSettings
            ).where(
                DriverSettings.telegram_id == user[0][0]
            ).values(
                limit=limit,
                access_limit=True
            ))
    await session.commit()

    return user[0]


async def access_debt_mode(session, user_id):
    """Получить статуса для смены в долг."""
    result = (await session.execute(
        select(
            DriverSettings.access_limit, DriverSettings.limit
        ).join(
            User
        ).where(
            User.telegram_id == user_id))).fetchone()

    return result


async def get_user_unique_phone(session, phone):
    """Получить одного пользователя по telegram_id."""
    user_phone = phone_formatting(phone)
    result = (await session.execute(select(
        User.first_name, User.middle_name, User.taxi_id, User.last_name, User.telegram_id
    ).where(User.phone == user_phone))).fetchone()

    return result


async def get_all_users(session):
    """Получить список пользователей."""
    result = (await session.execute(select(
        User.first_name, User.last_name, User.middle_name, User.phone, User.telegram_id))).fetchall()
    return result


async def get_user(session, user_id):
    """Получить одного пользователя по telegram_id."""
    result = (await session.execute(select(
        User.first_name, User.middle_name, User.taxi_id
    ).where(User.telegram_id == user_id))).fetchone()

    return result


async def add_user(session, user):
    """Запрос на добавление в БД."""
    result = await session.execute(insert(User).values(
        telegram_id=user.get('telegram_id'),
        first_name=user.get('first_name'),
        last_name=user.get('last_name'),
        middle_name=user.get('middle_name', ' '),
        phone=user.get('phone'),
        taxi_id=user.get('taxi_id')
    ).returning(
        User.first_name, User.last_name, User.middle_name)
    )
    await session.commit()
    return result.first()


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
