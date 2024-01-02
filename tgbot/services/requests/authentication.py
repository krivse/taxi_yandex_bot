import logging
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import pickle

from tgbot.services.requests.settings_driver import options_driver

from aiogram.types import Message


async def send_code_bot(obj, session):
    # отправление сообщения админу для ввода кода
    admin = obj.bot.get('config').tg_bot.admin_ids[0]
    await obj.bot.send_message(chat_id=admin, text='Ожидайте код для авторизация!')

    # передача состояния администратору для ввода кода и записи в очередь !
    await obj.bot.get('dp').storage.set_state(
        chat=admin, user=admin, state='CodeConfirmState:code')
    queue = obj.bot.get('queue')
    # запрос на получение пароля из бд
    from tgbot.models.query import get_account_password
    password = await get_account_password(session)

    return password, queue


def authentication_requests(queue, pass_park):
    """Авторизация в парке"""
    browser = options_driver()
    wait = WebDriverWait(browser, 1000)

    # Указываем URL-адрес для входа в систему
    current_park = 'https://fleet.yandex.ru/'
    status_requests = {}

    try:
        browser.get(current_park)
        # Дожидаемся загрузки страницы и нажимает на кнопку смены логина
        change_username = wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'button')))
        change_username.click()

        # перевод курсора на ввод почты
        choose_email = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-type="login"]')))
        choose_email.click()

        # ввод юзернейма
        input_username = wait.until(EC.visibility_of_element_located((By.ID, 'passp-field-login')))
        input_username.clear()
        input_username.send_keys('telbot1')
        # клик на кнопку подверждения логина
        enter_login = wait.until(EC.visibility_of_element_located((By.ID, 'passp:sign-in')))
        enter_login.click()
        # ввод пароля
        password = wait.until(EC.visibility_of_element_located((By.ID, 'passp-field-passwd')))
        password.clear()
        password.send_keys(pass_park)
        # клик на кнопку подверждения пароля
        enter_password = wait.until(EC.element_to_be_clickable((By.ID, 'passp:sign-in')))
        enter_password.click()

        # кнопка потвердить вход по номеру
        confirm = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'Button2_type_submit')))
        confirm.click()

        # ввод кода из смс
        enter_code = wait.until(EC.element_to_be_clickable((By.ID, 'passp-field-phoneCode')))
        code = queue.get()
        enter_code.send_keys(code)
        # ожидание ввода пароля в течение 300 секунд
        WebDriverWait(browser, 300).until(EC.staleness_of(enter_code))

        # клик на кнопку "Далее"
        # button_next = browser.find_element(by=By.CLASS_NAME, value='Button2_type_submit')
        # button_next.click()

        # выбор парка такси
        # choice_park = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'ParkButton_container__ALtGi')))
        # park = browser.find_element(by=By.TAG_NAME, value='span').text
        # if park == 'Фартовый':
        #     choice_park.click()

        # сохранение куки после авторизации для дальнейших запросов
        pickle.dump(browser.get_cookies(), open(f'{os.path.dirname(os.path.abspath(__file__))}/cookies', 'wb'))
        status_requests['status'] = 201

        return status_requests

    except TimeoutException:
        logging.error('TimeoutException. Время ожидания поиска элемента истекло!')
        status_requests['status'] = 400
        status_requests['message'] = 'Время ожидания поиска элемента истекло!'
        return status_requests
    except TimeoutError as ex:
        logging.error(f'TimeoutError. Время ожидания истекло и возникла ошибка времени ожидания: {ex}')
        status_requests['status'] = 400
        status_requests['message'] = f'Время ожидания истекло и возникла ошибка времени ожидания: {ex}'
        return status_requests
    except Exception as ex:
        logging.error(f'Exception. Ошибка {ex}')
        status_requests['status'] = 400
        status_requests['message'] = f'Время ожидания истекло и возникла ошибка времени ожидания: {ex}'
        return status_requests
    except NoSuchElementException as ex:
        logging.error(f'NoSuchElementException. Возможные проблемы c авторизацией по прямому запросу: {ex}')
        status_requests['status'] = 400
        status_requests['message'] = f'Возможные проблемы c авторизацией по прямому запросу!: {ex}'
        return status_requests
    finally:
        browser.close()
        browser.quit()
