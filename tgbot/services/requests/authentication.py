import logging
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import pickle

from tgbot.services.requests.settings_driver import options_driver


def authentication_requests(queue, pass_park):
    """Авторизация в парке"""
    browser = options_driver()
    wait = WebDriverWait(browser, 30)

    # Указываем URL-адрес для входа в систему
    current_park = 'https://fleet.yandex.ru/'
    try:
        browser.get(current_park)
        # Дожидаемся загрузки страницы и нажимает на кнопку смены логина
        change_username = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'Button2-Content')))
        change_username.click()

        # перевод курсора на ввод почты
        choose_email = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-type="login"]')))
        choose_email.click()

        # ввод юзернейма
        input_username = wait.until(EC.presence_of_element_located((By.ID, 'passp-field-login')))
        input_username.clear()
        input_username.send_keys('telbot1')
        # клик на кнопку подверждения логина
        enter_login = wait.until(EC.presence_of_element_located((By.ID, 'passp:sign-in')))
        enter_login.click()
        time.sleep(3)
        # ввод пароля
        password = wait.until(EC.presence_of_element_located((By.ID, 'passp-field-passwd')))
        password.clear()
        password.send_keys(pass_park)
        # клик на кнопку подверждения пароля
        enter_password = wait.until(EC.element_to_be_clickable((By.ID, 'passp:sign-in')))
        enter_password.click()

        # кнопка потвердить вход по номеру
        time.sleep(2)
        confirm = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'Button2_type_submit')))
        confirm.click()

        # ввод кода из смс
        enter_code = wait.until(EC.element_to_be_clickable((By.ID, 'passp-field-phoneCode')))
        code = queue.get()
        enter_code.send_keys(code)
        # ожидание ввода пароля в течении 300 секунд
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
        return True
    except TimeoutException:
        logging.error('TimeoutException. Время ожидания поиска элемента истекло!')
    except TimeoutError as ex:
        logging.error(f'TimeoutError. Время ожидания истекло и возникла ошибка времени ожидания: {ex}')
    except Exception as ex:
        logging.error(f'Exception. Ошибка {ex}')
    except NoSuchElementException:
        return 'NoSuchElementException. Возможные проблемы c авторизацией по прямому запросу!'
    finally:
        browser.close()
        browser.quit()