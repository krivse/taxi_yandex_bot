import logging
import os
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tgbot.services.requests.settings_driver import add_cookies, options_driver

from dotenv import load_dotenv


load_dotenv()


def change_limit_requests(phone, limit, url=None):
    browser = options_driver()
    wait = WebDriverWait(browser, 30)

    # Указываем URL-адрес для входа в систему
    if url is None:
        current_park = f'https://fleet.yandex.ru/drivers?status=working&park_id={os.getenv("X_Park_ID")}'
    else:
        current_park = f'https://fleet.yandex.ru/drivers/{url}/details?park_id={os.getenv("X_Park_ID")}'

    status_requests = {}

    try:
        browser.get(current_park)
        status = add_cookies(browser, wait)
        if not status:
            status_requests['status'] = 401
            return status_requests

        if url is None:
            # выбор парка
            # choice_park = browser.find_element(by=By.CLASS_NAME, value='ParkButton_container__ALtGi')
            # choice_park.click()
            # поиск водителя
            search_driver = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Textinput-Control')))
            search_driver.send_keys(phone)
            choice_driver = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'PNVeph')))
            choice_driver.click()

        # поиск поля для изменения лимита
        change_limit = wait.until(EC.element_to_be_clickable((By.NAME, 'accounts.balance_limit')))
        change_limit.clear()
        # очистить поле
        change_limit.send_keys([Keys.BACKSPACE] * 10)
        change_limit.send_keys(limit)
        # сохранить новый лимит водителя
        save_button = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//div[starts-with(@class, 'DriverForm_button__')]"
        )))
        click_on_buttons = WebDriverWait(save_button, 30).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'Button')))
        click_on_buttons.click()
        status_requests['status'] = 200

        return status_requests

    except TimeoutException:
        logging.error('TimeoutException. Время ожидания поиска элемента истекло!')
        status_requests['status'] = 400
        status_requests['message'] = 'Время ожидания поиска элемента истекло!'
        return status_requests
    except TimeoutError as ex:
        logging.error(f'TimeoutError. Время ожидания истекло и возникла ошибка времени ожидания: {ex}')
        status_requests['status'] = 400
        status_requests['message'] = f'Время ожидания истекло и возникла ошибка времени ожидания'
        return status_requests
    except Exception as ex:
        logging.error(f'Exception. Ошибка {ex}')
        status_requests['status'] = 400
        status_requests['message'] = 'Ошибка при выполнении запроса!'
        return status_requests
    except NoSuchElementException:
        status_requests['status'] = 400
        status_requests['message'] = 'Возможные проблемы c авторизацией по прямому запросу!'
        return status_requests
    finally:
        browser.close()
        browser.quit()
