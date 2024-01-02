from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.dispatcher import Dispatcher

from sqlalchemy.exc import IntegrityError

from tgbot.keyboards.inline_admin import access, access_debt, account, agree_text, edit_cancel, reset_user_removal, \
    help_keyboard
from tgbot.keyboards.user_button import choose_menu_for_user
from tgbot.misc.states import AccountParkState, CodeConfirmState, DeleteState, EditState, HelpState, NewSendState, \
    RegisterState
from tgbot.models.query import (add_or_update_limit_user, add_or_update_text_for_help, add_user, delete_access_user,
                                drop_user, get_all_users, get_user_unique_phone, update_account_password)
from tgbot.services.api.get_list_drivers import get_driver_profile
from tgbot.services.set_commands import commands, set_default_commands


async def admin_start(message: Message):
    """Приветственное сообщение для администратора."""
    await message.answer(f'Приветствую, {message.from_user.first_name}(admin)!')
    # команды для администратора.
    await set_default_commands(
        message.bot,
        user_id=message.from_id
    )


async def get_user(message: Message, session, state: FSMContext):
    # Из функции get_driver_profile получаем данные о водителе.
    phone = message.text

    if phone.isdigit():
        user_unique = await get_user_unique_phone(session, phone)
        if not user_unique:
            # ключи для выполнения запрос к API Yandex
            header = message.bot.get('config').misc
            user = await get_driver_profile(phone, header)
            admin = message.bot.get('config').tg_bot.admin_ids[0]
            # Делаем проверку на получение пользователя.
            if not isinstance(user, str):
                # сбрасываем состояние водителя.
                await state.finish()
                # Отправляем админу заявку на добавление пользователя.
                msg = await message.bot.send_message(
                    chat_id=admin,
                    text=f'{user[0]} {user[1]} {user[2]}\n'
                         f'+{user[3]}',
                    reply_markup=access
                )
                # Добавляем юзера в хранилище dp.
                await message.bot.get('dp').storage.update_data(
                    chat=admin,
                    user=user[3],
                    data={'first_name': user[0],
                          'last_name': user[1],
                          'middle_name': user[2],
                          'phone': user[3],
                          'taxi_id': user[4],
                          'telegram_id': message.from_user.id,
                          'message_id': msg.message_id
                          }
                )
                # Отправка сообщения пользователю (водителю).
                await message.answer(
                    text='Заявка отправлена в парк. Ожидайте...'
                )
            # Пользовтаель не найден.
            else:
                await message.answer(
                    text=user
                )
        elif user_unique:
            await state.finish()
            await message.answer('В доступе отказано. Телефонный номер уже привязан к другому аккаунту, '
                                 'обратитесь в техподдержку парка.')
    else:
        await message.answer(f'Попробуйте ещё раз и вводите только цифры')


async def add_or_refuse_user(call: CallbackQuery, session):
    """Добавление пользователя в БД."""
    phone = int(call.message.text.split('\n').pop(1))
    admin = call.message.bot.get('config').tg_bot.admin_ids[0]

    # получение user из storage.
    user = await call.bot.get('dp').storage.get_data(chat=admin, user=phone)
    # очистка usera из storage.
    await call.bot.get('dp').storage.finish(chat=admin, user=phone)

    if call.data == 'add':
        # запроса на добавление пользователя в бд.
        try:
            user_add = await add_user(session, user)
            telegram_id = user.get('telegram_id')
            first_name = user.get("first_name")
            middle_name = user.get("middle_name", " ")
            await call.message.bot.send_message(
                chat_id=user.get('telegram_id'),
                text=f'{first_name} {middle_name} доступ разрешен. '
                     'Теперь Вы можете управлять своим аккаунтом в Яндекс Про.',
                reply_markup=await choose_menu_for_user(session, telegram_id))
            await call.message.bot.send_message(
                chat_id=admin,
                text=f'Водитель {user_add[1]} {user_add[0]} {user_add[2]} добавлен в базу!')
        except IntegrityError:
            await call.message.bot.send_message(
                chat_id=user.get('telegram_id'),
                text='В доступе отказано. Телефонный номер уже привязан к другому аккаунту, '
                     'обратитесь в техподдержку парка.')
    elif call.data == 'reject':
        # вывод сообщения в случае если админ отказал добавить пользователя.
        await call.message.bot.send_message(chat_id=user.get('telegram_id'),
                                            text='В доступе отказано!')

    # удаление у админа клавиатуры и сообщения.
    await call.message.bot.delete_message(chat_id=admin, message_id=user.get('message_id'))


async def remove_user(message: Message, state: FSMContext):
    """Ввод номера телефона для удаления пользователя."""
    msg_delete_for_remove_user = await message.answer(
        'Введите номер телефона водителя, которого необходимо удалить.',
        reply_markup=reset_user_removal)
    await state.update_data(msg_delete_for_remove_user=msg_delete_for_remove_user.message_id)
    await DeleteState.phone.set()


async def removing_the_user(message: Message, session, state: FSMContext):
    """Удаление user из базы."""
    try:
        result = await drop_user(session, message.text, state)
        # если вернулся телефонный номер
        await message.answer(result)
    # некорректно введенный номер
    except ValueError:
        # сброс состояния, если пользователь вводит не числа.
        if not message.text.isdigit():
            await message.answer(f'Попробуйте ещё раз и вводите только цифры..')
        else:
            await message.answer(f'Введен некорректный номер телефона: {message.text}. '
                                 'Попробуйте ввести ещё раз..')


async def cancel_removal(call: CallbackQuery, state: FSMContext):
    """Отмена действия на удаление пользотваеля."""
    admin = call.message.bot.get('config').tg_bot.admin_ids[0]
    msg_delete = await state.get_data()
    await call.message.bot.delete_message(chat_id=admin,
                                          message_id=msg_delete.get('msg_delete_for_remove_user'))
    await state.finish()


async def get_drivers(message: Message, session):
    """Получить список водитель."""
    users = await get_all_users(session)
    list_driver = ''

    if users:
        for i, name in enumerate(users, start=1):
            if len(list_driver) + 250 >= 4096:
                await message.answer(list_driver)
                list_driver = ''
            list_driver += f'{i}. {name[1]} {name[0]} {name[3]}\n'
        await message.answer(list_driver)
    elif not users:
        await message.answer('Список водителей пуст!')


async def edit_driver(message: Message, state: FSMContext):
    """Команда для редактирования водителей."""
    msg_to_delete_debt = await message.answer('Отрицательный баланс для водителей', reply_markup=access_debt)

    await state.update_data(msg_to_delete_debt=msg_to_delete_debt.message_id)


async def on_of_off_debt(call: CallbackQuery, state: FSMContext):
    """Добавление / удаление смены в минус."""
    if call.data == 'on_debt':
        message = await call.message.answer(
            f'Для подключения "Смены в минус" введите номер телефона водителя', reply_markup=edit_cancel)
        await state.update_data(msg_to_delete_cancel_edit=message.message_id)
        # передаём состояние в функцию edit_on_debt
        await EditState.on_phone.set()
    elif call.data == 'off_debt':
        message = await call.message.answer(
            f'Для отключения "Смены в минус" введите номер телефона водителя', reply_markup=edit_cancel)
        await state.update_data(msg_to_delete_cancel_edit=message.message_id)
        # передаём состояние в функцию edit_off_debt
        await EditState.off_phone.set()


async def edit_on_debt(message: Message, session, state: FSMContext):
    """Обработка номера телефона и передача состояния в следующую функцию для изменения лимита."""

    # Из функции get_driver_profile получаем данные о водителе.
    phone = message.text

    if phone.isdigit():
        # получаем пользователя из бд
        user = await get_user_unique_phone(session, phone)
        if user is not None:
            await message.answer(f'Укажите лимит для {user[3]} {user[0]} {user[1]}')
            # передаём состояние в функцию edit_limit
            await EditState.limit.set()
            await state.update_data(taxi_id=user[2])
        elif user is None:
            await message.answer('Такого номера нет. Попробуйте ввести ещё раз..')
    else:
        await message.answer(f'Попробуйте ещё раз и вводите только цифры..')


async def edit_limit(message: Message, session, state: FSMContext):
    """Изменение лимита у водителя / запись в таблицу driver_setting."""

    # лимит для изменения
    limit = message.text if message.text[0] != '-' else message.text.replace('-', '')
    # ключ водителя из таксопарка
    taxi_id = (await state.get_data()).get('taxi_id')

    if limit.isdigit():
        # запрос на изменение отрицательного лимита
        telegram_id, first_name, middle_name = await add_or_update_limit_user(session, taxi_id, -int(limit))
        await message.answer(f'Для {first_name} {middle_name}, установлен лимит -{limit}')
        await message.bot.send_message(
            chat_id=telegram_id,
            text=f'{first_name} {middle_name}, смена в долг подключена! '
                 'Для использования нажмите на /start и выберите режим работы "Смена в долг"'
        )
        await state.finish()
    else:
        await message.answer(f'Попробуйте ещё раз и вводите только цифры')


async def edit_off_debt(message: Message, session, state: FSMContext):
    """Удаление возможности взять в смену в долг."""
    phone = message.text
    if phone.isdigit():
        first_name, middle_name, taxi_id, last_name, telegram_id = await get_user_unique_phone(session, phone)
        result = await delete_access_user(session, telegram_id)
        if not result:
            await message.answer(f'Водителю {first_name} {middle_name}: отключена "Смена в долг"')
        else:
            await message.answer('Непредвиденная ошибка! попробуйте снова /edit_user')
        await state.finish()
    else:
        await message.answer(f'Попробуйте ещё раз и вводите только цифры')


async def edit_cancel_dept(call: CallbackQuery, state: FSMContext):
    """Отменить действие на редактирование / удаление клавиатуры / информационного сообщения."""
    msg_to_delete_debt = (await state.get_data()).get('msg_to_delete_debt')
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_to_delete_debt)
    await state.finish()


async def edit_cancel_edit(call: CallbackQuery, state: FSMContext):
    """Отменить действие на редактирование / удаление клавиатуры / информационного сообщения."""
    msg_to_delete_debt = (await state.get_data()).get('msg_to_delete_debt')
    msg_to_delete_cancel_edit = (await state.get_data()).get('msg_to_delete_cancel_edit')
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_to_delete_debt)
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_to_delete_cancel_edit)
    await state.finish()


async def newsend(message: Message):
    """Рассылка сообщений всему парку."""
    await message.answer('Введите текст, который хотите отправить')
    await NewSendState.text.set()


async def newsend_text(message: Message, state: FSMContext):
    """Текст для отправки сообещния."""
    text = message.text
    msg_delete_for_newsend = await message.answer(text, reply_markup=agree_text)
    await state.update_data(text=text, msg_delete_for_newsend=msg_delete_for_newsend.message_id)


async def agree_or_cancel_send_text(call: CallbackQuery, session, state: FSMContext):
    """Отправить или отменить рассылку."""
    data = await state.get_data()
    msg_delete_for_newsend = data.get('msg_delete_for_newsend')
    text = data.get('text')

    if call.data == 'agree_send':
        await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_delete_for_newsend)
        users = await get_all_users(session)
        for user in users:
            from aiogram.utils.exceptions import BotBlocked
            try:
                await call.message.bot.send_message(chat_id=user[4], text=text)
            except BotBlocked as e:
                print('BOTBLOCKED', user[1], user[2], user[3], user[4])
        await call.message.answer('Была произведена рассылка сообщений')
    elif call.data == 'cancel_send':
        await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_delete_for_newsend)
    await state.finish()


async def get_code_confirm(message: Message):
    """Получение кода от пользователя."""
    code = message.text
    message.bot.get('queue').put(code)


async def change_password(message: Message, state: FSMContext):
    """Команда для смены пароля парка."""
    msg_delete_to_change_pass = await message.answer('Введите новый пароль!', reply_markup=account)
    await state.update_data(msg_delete_to_change_pass=msg_delete_to_change_pass.message_id)
    await AccountParkState.password.set()


async def new_password(message: Message, session, state: FSMContext):
    """Добавление нового пароля в БД."""
    password = message.text
    new_pass = await update_account_password(session, password)
    if password not in commands:
        await message.answer(f'Ваш новый пароль: {new_pass}')
        await state.finish()
    else:
        await message.answer('Содержание пароля не может соответсовать названию команды! Попробуйте снова..')


async def cancel_change_password(call: CallbackQuery, state: FSMContext):
    """Отмена действия на изменение пароля."""
    msg_delete_to_change_pass = (await state.get_data()).get('msg_delete_to_change_pass')
    await call.message.bot.delete_message(chat_id=call.from_user.id, message_id=msg_delete_to_change_pass)
    await state.finish()


async def configure_help(message: Message):
    """Команда для редактирования текста справки."""
    await message.answer('Введите текст, который нужно добавить или обновить')
    await HelpState.text.set()


async def enter_text_for_help(message: Message, state: FSMContext):
    """Ввод текста для команды /configure_help."""
    text = message.text
    text_for_delete_help = message.message_id

    if text not in commands:
        # Отправка текста и клавиатуры для подтверждения или отмены операции
        msg_delete = await message.answer(text=text, reply_markup=help_keyboard)
        await state.update_data(
            message_for_delete_help=msg_delete.message_id,
            text_for_delete_help=text_for_delete_help,
            text_help=text
        )
        await state.reset_state(with_data=False)
    else:
        await message.answer(f'Вы ввели название команды {message.text}... Операция отменена.\n'
                             'Вызовите команду повторно и вводите текст отличающийся от названия команды')
        await state.finish()


async def confirm_text_for_help(call: CallbackQuery, session, state: FSMContext):
    """Подтверждение ввода текста и запись в бд."""
    data = await state.get_data()

    # message_id's для удаления временных сообщений
    msg_for_delete = data.get('message_for_delete_help')
    text_for_delete = data.get('text_for_delete_help')

    # запись данных
    text = data.get('text_help')
    text = await add_or_update_text_for_help(session, text)
    await call.message.answer('Проверьте текст и при необходимости воспользуйтесь командой повторно /configure_help\n'
                              f'{text}')

    # удаление временных сообщений
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_for_delete)
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=text_for_delete)
    await state.finish()


async def cancel_text_for_help(call: CallbackQuery, state: FSMContext):
    """Отмена действия по вводу текста для /configure_help."""
    data = await state.get_data()

    # message_id's для удаления временных сообщений
    msg_for_delete = data.get('message_for_delete_help')
    text_for_delete = data.get('text_for_delete_help')

    # удаление временных сообщений
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=msg_for_delete)
    await call.message.bot.delete_message(chat_id=call.message.chat.id, message_id=text_for_delete)
    await state.finish()


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, CommandStart(), state='*', is_admin=True)
    dp.register_message_handler(get_user, state=RegisterState.phone)
    dp.register_callback_query_handler(add_or_refuse_user, text=['add', 'reject'])
    dp.register_message_handler(remove_user, Command('remove_user'), is_admin=True)
    dp.register_message_handler(removing_the_user, state=DeleteState.phone, is_admin=True)
    dp.register_callback_query_handler(cancel_removal, text='cancel', state=DeleteState.phone, is_admin=True)
    dp.register_message_handler(get_drivers, Command('users'), is_admin=True)
    dp.register_message_handler(edit_driver, Command('edit_user'), is_admin=True)
    dp.register_callback_query_handler(on_of_off_debt, text=['on_debt', 'off_debt'], is_admin=True)
    dp.register_message_handler(edit_on_debt, state=EditState.on_phone, is_admin=True)
    dp.register_message_handler(edit_off_debt, state=EditState.off_phone, is_admin=True)
    dp.register_message_handler(edit_limit, state=EditState.limit, is_admin=True)
    dp.register_callback_query_handler(edit_cancel_dept, text='cancel_edit', is_admin=True)
    dp.register_callback_query_handler(edit_cancel_edit, state=EditState, text='edit_cancel', is_admin=True)
    dp.register_message_handler(newsend, Command('newsend'), is_admin=True)
    dp.register_message_handler(newsend_text, state=NewSendState.text, is_admin=True)
    dp.register_callback_query_handler(
        agree_or_cancel_send_text, state=NewSendState.states, text=['agree_send', 'cancel_send'], is_admin=True)
    dp.register_message_handler(get_code_confirm, state=CodeConfirmState.code)
    dp.register_message_handler(change_password, Command('change_password'), is_admin=True)
    dp.register_message_handler(new_password, state=AccountParkState.password, is_admin=True)
    dp.register_callback_query_handler(
        cancel_change_password, state=AccountParkState.states, text='cancel_password', is_admin=True)
    dp.register_message_handler(configure_help, Command('configure_help'), is_admin=True)
    dp.register_message_handler(enter_text_for_help, state=HelpState.text, is_admin=True)
    dp.register_callback_query_handler(confirm_text_for_help, text='confirm_help', is_admin=True)
    dp.register_callback_query_handler(cancel_text_for_help, text='cancel_help', is_admin=True)
