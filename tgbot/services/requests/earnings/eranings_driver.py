import logging
import os

from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tgbot.services.requests.general_requests import general_calendars
from tgbot.services.requests.settings_driver import add_cookies, options_driver

from dotenv import load_dotenv


load_dotenv()


def earnings_driver_requests(phone, interval, url=None):
    browser = options_driver()
    wait = WebDriverWait(browser, 30)

    if url is None:
        current_park = f'https://fleet.yandex.ru/contractors?status=working&park_id={os.getenv("X_Park_ID")}'
    else:
        current_park = f'https://fleet.yandex.ru/contractors/{url}/income?park_id={os.getenv("X_Park_ID")}'

    status_requests = {}

    try:
        browser.get(current_park)
        status = add_cookies(browser, wait)

        if not status:
            status_requests['status'] = 401
            return status_requests

        if url is None:
            # поиск водителя
            search_driver = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Textinput-Control')))
            search_driver.send_keys(phone)
            choice_driver = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'PNVeph')))
            choice_driver.click()

            # поиск и переход на вкладку "Заработок"
            tab_earnings = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Заработок')))
            tab_earnings.click()

        # открыть календарь для установки периода
        general_calendars(wait, interval, browser)

        earnings_list = []
        data = wait.until(EC.visibility_of_all_elements_located((By.TAG_NAME, 'dd')))
        for i in data:
            earnings_list.append(i.text)
        status_requests['status'] = 200
        status_requests['earnings'] = earnings_list

        return status_requests

    except TimeoutException:

        logging.error('TimeoutException. Время ожидания поиска элемента истекло!')

        status_requests['status'] = 400

        status_requests['message'] = 'Время ожидания поиска элемента истекло!'

        return status_requests

    except Exception as ex:
        logging.error(f'Exception. Ошибка {ex}')
        status_requests['status'] = 400
        status_requests['message'] = 'Ошибка при выполнении запроса!'
        return status_requests
    except NoSuchElementException as nse:
        logging.error(f'NoSuchElementException. Ошибка {nse}')
        status_requests['status'] = 400
        status_requests['message'] = 'Элемент не найден!'
        return status_requests
    except ElementClickInterceptedException as ece:
        logging.error(f'ElementClickInterceptedException. Ошибка {ece}')
        status_requests['status'] = 400
        status_requests['message'] = 'Элемент не взаимодействует!'
    finally:
        browser.close()
        browser.quit()
