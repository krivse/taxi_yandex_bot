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


def change_limit_requests(phone, limit):
    browser = options_driver()
    wait = WebDriverWait(browser, 30)


    # Указываем URL-адрес для входа в систему
    current_park = f'https://fleet.yandex.ru/drivers?status=working&park_id={os.getenv("X_Park_ID")}'
    try:
        browser.get(current_park)
        status = add_cookies(browser)
        if not status:
            return False

        # выбор парка
        # choice_park = browser.find_element(by=By.CLASS_NAME, value='ParkButton_container__ALtGi')
        # choice_park.click()

        # поиск водителя
        search_driver = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'Textinput-Control')))
        search_driver.send_keys(phone)
        time.sleep(0.5)
        choice_driver = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'PNVeph')))
        choice_driver.click()
        # поиск поля для изменения лимита
        change_limit = wait.until(EC.element_to_be_clickable((By.NAME, 'accounts.balance_limit')))
        change_limit.clear()
        # очистить поле
        time.sleep(0.5)
        change_limit.send_keys([Keys.BACKSPACE] * 10)
        change_limit.send_keys(limit)
        # сохранить новый лимит водителя
        save_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'Button2_type_submit')))
        save_button.click()

        # сохранить ссылку на страницу водителя
        for_save_driver_url = browser.find_element(
            By.XPATH, "//div/a[starts-with(@class, 'CarInfo_link__')]").get_attribute('href')
        parse_driver_url = for_save_driver_url.split('/')[4]

        return 200, parse_driver_url
    except TimeoutException:
        logging.error('TimeoutException. Время ожидания поиска элемента истекло!')
        return False
    except TimeoutError as ex:
        logging.error(f'TimeoutError. Время ожидания истекло и возникла ошибка времени ожидания: {ex}')
    except Exception as ex:
        logging.error(f'Exception. Ошибка {ex}')
    except NoSuchElementException:
        return 'NoSuchElementException. Возможные проблемы c авторизацией по прямому запросу!'
    finally:
        browser.close()
        browser.quit()


def change_limit_by_url_driver_requests(limit, url_driver):
    browser = options_driver()
    wait = WebDriverWait(browser, 30)

    page_driver = f'https://fleet.yandex.ru/drivers/{url_driver}/details?park_id={os.getenv("X_Park_ID")}'

    try:
        browser.get(page_driver)
        status = add_cookies(browser)

        if not status:
            return False

        # поиск поля для изменения лимита
        change_limit = wait.until(EC.element_to_be_clickable((By.NAME, 'accounts.balance_limit')))
        change_limit.clear()
        # очистить поле
        time.sleep(0.5)
        change_limit.send_keys([Keys.BACKSPACE] * 10)
        change_limit.send_keys(limit)
        # сохранить новый лимит водителя
        save_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'Button2_type_submit')))
        save_button.click()

        return 200
    except TimeoutException:
        logging.error('TimeoutException. Время ожидания поиска элемента истекло!')
        return False
    except TimeoutError as ex:
        logging.error(f'TimeoutError. Время ожидания истекло и возникла ошибка времени ожидания: {ex}')
    except Exception as ex:
        logging.error(f'Exception. Ошибка {ex}')
    except NoSuchElementException:
        return 'NoSuchElementException. Возможные проблемы c авторизацией по прямому запросу!'
    finally:
        browser.close()
        browser.quit()
