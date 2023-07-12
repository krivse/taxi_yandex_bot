import logging
import os
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from tgbot.services.requests.settings_driver import add_cookies, options_driver

from dotenv import load_dotenv

load_dotenv()


def earnings_driver_requests(phone, interval, url=None):
    browser = options_driver()
    wait = WebDriverWait(browser, 30)

    if url is None:
        current_park = f'https://fleet.yandex.ru/drivers?status=working&park_id={os.getenv("X_Park_ID")}'
    else:
        current_park = f'https://fleet.yandex.ru/drivers/{url}/income?park_id={os.getenv("X_Park_ID")}'

    try:
        browser.get(current_park)
        status = add_cookies(browser)

        if not status:
            return False

        parse_id_driver_url = None
        if url is None:
            # поиск водителя
            search_driver = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'Textinput-Control')))
            search_driver.send_keys(phone)
            browser.implicitly_wait(0.5)
            time.sleep(1)
            choice_driver = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'PNVeph')))
            choice_driver.click()
            time.sleep(1)
            # поиск вкладки "Заказы" и сохранение id водителя
            for_save_driver_url = wait.until(EC.presence_of_element_located((
                By.XPATH, "//a[starts-with(@href, '/drivers/')]"))).get_attribute('href')
            parse_id_driver_url = for_save_driver_url.split('/')[4]
            # поиск и переход на вкладку "Заказы"
            tab_order = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Заработок')))
            tab_order.click()

        popup_cal = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//span[contains(@class, 'DateRangeInput_alignStart__')]")))
        popup_cal.click()
        time.sleep(1)
        # find_month = browser.find_elements(By.XPATH, f"//span[starts-with(text(), {interval.get('start_month')})]")
        # find_day = find_month.find_element(By.XPATH, f"//span[starts-with(text(), {interval.get('start_day')})]")
        # find_day = browser.find_elements(By.CLASS_NAME, 'Day')
        calendars = browser.find_elements(By.CLASS_NAME, 'Calendar')
        for calendar in range(len(calendars)):
            find_month = calendars[calendar].find_element(By.TAG_NAME, 'span').text
            if find_month.startswith(interval.get('start_month')):
                find_day = calendars[calendar].find_elements(By.TAG_NAME, 'span')
                for day in find_day:
                    if day.text == interval.get('start_day'):
                        day.click()
            if find_month.startswith(interval.get('end_month')):
                find_day = calendars[calendar].find_elements(By.TAG_NAME, 'span')
                for day in find_day:
                    if day.text == interval.get('end_day'):
                        day.click()
        confirm_date = browser.find_element(By.CLASS_NAME, 'Modal-Content'
                                            ).find_element(By.CLASS_NAME, 'Button2-Content')
        confirm_date.click()

        time.sleep(2)
        earnings_list = []
        first_block = browser.find_elements(By.TAG_NAME, "dd")
        for i in first_block:
            earnings_list.append(i.text)
        return 200, parse_id_driver_url, earnings_list

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
