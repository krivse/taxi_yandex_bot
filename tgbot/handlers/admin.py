from sqlalchemy.exc import IntegrityError

from aiogram.dispatcher.filters import CommandStart, Command
from aiogram.dispatcher import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext

from tgbot.keyboards.inline import access, reset_user_removal
from tgbot.keyboards.user_button import menu
from tgbot.misc.states import DeleteState, RegisterState
from tgbot.models.query import add_user, drop_user, get_all_users, get_user_unique_phone
from tgbot.services.api_requests import get_driver_profile
from tgbot.services.set_commands import set_default_commands


async def admin_start(message: Message):
    # приветственное сообщение для администратора.
    await message.answer(f'Приветствую, {message.from_user.first_name}(admin)!')
    # команды для администратора.
    await set_default_commands(
        message.bot,
        user_id=message.from_id
    )


async def get_user(message: Message, session, state: FSMContext):
    # Из функции get_driver_profile получаем данные о водителе.
    phone = message.text
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
            await call.message.bot.send_message(
                chat_id=user.get('telegram_id'),
                text='Доступ разрешен. Теперь вы можете переключать способ оплаты за заказы в Яндекс Про.',
                reply_markup=menu)
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
    await call.message.edit_reply_markup()
    await call.message.bot.delete_message(chat_id=admin, message_id=user.get('message_id'))


async def remove_user(message: Message, state: FSMContext):
    """Ввод номера телефона для удаления пользователя."""
    msg_delete = await message.answer('Введите номер телефона водителя, которого необходимо удалить.',
                                      reply_markup=reset_user_removal)
    await state.update_data(msg_delete=msg_delete.message_id)
    await DeleteState.phone.set()


async def cancel_removal(call: CallbackQuery, state: FSMContext):
    """Отмена действия на удаление пользотваеля."""
    admin = call.message.bot.get('config').tg_bot.admin_ids[0]
    await call.message.edit_reply_markup()
    msg_delete = await state.get_data()
    await call.message.bot.delete_message(chat_id=admin,
                                          message_id=msg_delete.get('msg_delete'))
    await state.finish()


async def removing_the_user(message: Message, session, state: FSMContext):
    """Удаление user из базы."""
    try:
        phone = await drop_user(session, message.text, state)
        # если вернулся телефонный номер
        await message.answer(phone)
    # некорректно введенный номер
    except ValueError:
        # сброс состояния, если пользователь вводит не числа.
        if message.text == '/remove_user' or not message.text.isdigit():
            await state.reset_state()
            await message.answer(f'Попробуйте ещё раз и вводите только цифры /remove_user')
        else:
            await message.answer(f'Введен некорректный номер телефона: {message.text}. '
                                 'Попробуйте ввести ещё раз..')


async def drivers(message: Message, session):
    """Получить список водитель."""
    users = await get_all_users(session)
    list_driver = ''
    if users:
        for i, name in enumerate(users, start=1):
            list_driver += f'{i}. {name[1]} {name[0]} {name[3]}\n'
        await message.answer(list_driver)
    elif not users:
        await message.answer('Список водителей пуст!')


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, CommandStart(), state='*', is_admin=True)
    dp.register_message_handler(get_user, state=RegisterState.phone)
    dp.register_callback_query_handler(add_or_refuse_user, text=['add', 'reject'])
    dp.register_message_handler(remove_user, Command('remove_user'), is_admin=True)
    dp.register_message_handler(removing_the_user, state=DeleteState.phone, is_admin=True)
    dp.register_callback_query_handler(cancel_removal, text='cancel', state=DeleteState.phone, is_admin=True)
    dp.register_message_handler(drivers, Command('users'), is_admin=True)
