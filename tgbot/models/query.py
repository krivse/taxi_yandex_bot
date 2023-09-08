from sqlalchemy import delete, insert, select, update

from tgbot.models.models import User, DriverSettings, AccountPark, Help
from tgbot.services.other_functions.phone_formatter import phone_formatting


async def add_or_update_smz_user(session, user_id, swtich):
    """Подключение или отключение услуги СМЗ."""
    # возвращается две записи из бд, если в обеих таблицах есть связанная запись.
    user = (await session.execute(
        select(
            DriverSettings.telegram_id, User.first_name, User.middle_name
        ).join(
            User
        ).where(
            User.telegram_id == user_id
        ).union_all(
            select(
                User.telegram_id, User.first_name, User.middle_name
            ).where(
                User.telegram_id == user_id)

        ))).fetchall()

    # если записи нет в driver_settings, то она создается
    result = None
    if len(user) == 1:
        result = (await session.execute(
            insert(
                DriverSettings
            ).values(
                telegram_id=user[0][0],
                smz=swtich
            ).returning(DriverSettings.smz))).scalar()
    # если такая запись есть, то она обновляется
    elif len(user) > 1:
        result = (await session.execute(
            update(
                DriverSettings
            ).where(
                DriverSettings.telegram_id == user[0][0]
            ).values(
                smz=swtich
            ).returning(DriverSettings.smz))).scalar()
    await session.commit()

    return result


async def switch_smz(session, user_id):
    """Получить статуса для смены в долг."""
    result = (await session.execute(
        select(
            DriverSettings.smz
        ).join(
            User
        ).where(
            User.telegram_id == user_id))).scalar()

    return result


async def get_info_from_help(session):
    """Получение поля text из таблицы Help."""
    exists = await session.get(Help, 1)

    return exists


async def add_or_update_text_for_help(session, text):
    """Добавление текста для команды /configure_help."""
    exists = await get_info_from_help(session)

    if exists is None:
        result = await session.execute(
            insert(
                Help
            ).values(
                text=text
            ).returning(Help.text)
        )
        await session.commit()
        return result.fetchone()[0]

    elif exists is not None:
        result = await session.execute(
            update(
                Help
            ).where(
                Help.id == exists.id
            ).values(
                text=text
            ).returning(Help.text)
        )

        await session.commit()
        return result.fetchone()[0]


async def add_url_driver(session, driver_url, phone):
    """Добавление url страницы водителя парка."""
    user = (await session.execute(
        select(
            DriverSettings.telegram_id
        ).join(
            User
        ).where(
            User.phone == phone
        ).union_all(
            select(
                User.telegram_id
            ).where(
                User.phone == phone)
        ))).fetchall()
    print(user)

    # если записи нет в driver_settings, то она создается
    if len(user) == 1:
        await session.execute(
            insert(
                DriverSettings
            ).values(
                telegram_id=user[0][0],
                url_driver_limit=driver_url
            ))
    # если такая запись есть, то она обновляется
    elif len(user) > 1:
        await session.execute(
            update(
                DriverSettings
            ).where(
                DriverSettings.telegram_id == user[0][0]
            ).values(
                url_driver_limit=driver_url
            ))

    await session.commit()


async def get_url_driver_limit(session, phone):
    """Получить url страницы водителя в парке / вкладка "Детали"."""
    result = (await session.execute(
        select(
            DriverSettings.url_driver_limit
        ).join(
            User
        ).where(
            User.phone == phone
        ))).fetchone()

    return result


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

        await session.commit()
        return result

    if exists is not None:
        result = (await session.execute(
            update(
                AccountPark
            ).where(
                AccountPark.id == exists.id
            ).values(
                password=password
            ).returning(AccountPark.password))).scalar()

        await session.commit()
        return result


async def get_account_password(session):
    """Получение пароля парка."""
    result = (await session.get(
        AccountPark, 1)).password

    return result


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

    # возвращается две записи из бд, если в обеих таблицах есть связанная запись.
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
        User.first_name, User.middle_name, User.taxi_id, User.phone
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
