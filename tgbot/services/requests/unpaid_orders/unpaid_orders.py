import logging
import os
import time

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from tgbot.services.requests.settings_driver import add_cookies, options_driver

from dotenv import load_dotenv

load_dotenv()


def unpaid_orders_requests(phone, interval, url=None):
    browser = options_driver()
    wait = WebDriverWait(browser, 30)

    if url is None:
        current_park = f'https://fleet.yandex.ru/drivers?status=working&park_id={os.getenv("X_Park_ID")}'
    else:
        current_park = f'https://fleet.yandex.ru/drivers/{url}/orders?park_id={os.getenv("X_Park_ID")}'

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
            tab_order = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Заказы')))
            tab_order.click()

        if interval is not None:
            popup_calendar = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//span[contains(@class, 'DateRangeInput_alignStart')]")))
            popup_calendar.click()
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
        actions = ActionChains(browser)
        filters = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'Select__control')))
        for i in filters:

            if i.text == 'Статус':
                time.sleep(1)
                i.click()
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(0.2)
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(0.11)
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(0.1)
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(0.1)
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(0.05)
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(0.07)
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(0.1)
                actions.send_keys(Keys.ENTER).perform()
                st = i.find_element(By.CLASS_NAME, 'Select__multi-value')
                time.sleep(1)
                st.click()
                statuses = browser.find_elements(By.CLASS_NAME, 'Select__multi-value__remove')
                for complete in statuses:
                    if complete.get_dom_attribute('aria-label').strip('Remove ') != 'Выполнен':
                        time.sleep(0.1)
                        complete.click()
                time.sleep(1)

            elif i.text == 'Тип оплаты':
                i.click()
                time.sleep(0.1)
                actions.send_keys([Keys.ENTER]).perform()
                time.sleep(0.12)
                actions.send_keys([Keys.ENTER]).perform()
                time.sleep(0.1)
                actions.send_keys([Keys.ENTER]).perform()
                time.sleep(0.1)
                actions.send_keys([Keys.ENTER]).perform()
                time.sleep(0.12)
                actions.send_keys([Keys.ENTER]).perform()
                time.sleep(0.2)
                actions.send_keys([Keys.ENTER]).perform()
                time.sleep(0.1)
                actions.send_keys([Keys.ENTER]).perform()
                st = i.find_element(By.CLASS_NAME, 'Select__multi-value')
                st.click()
                statuses = browser.find_elements(By.CLASS_NAME, 'Select__multi-value__remove')
                for complete in statuses:
                    cashless = complete.get_dom_attribute('aria-label').strip('Remove ')
                    if cashless not in ['Безналичные', 'Корп. счёт', 'Карта', 'Выполнен']:
                        time.sleep(0.1)
                        complete.click()

        while True:
            try:
                browser.implicitly_wait(5)
                # time.sleep(2)
                exists_el = WebDriverWait(browser, 3).until(EC.visibility_of_element_located(
                    (By.XPATH, "//span[contains(text(), 'Загрузить ещё')]"))
                )
                # exists_el = browser.find_element(By.XPATH, "//span[contains(text(), 'Загрузить ещё')]")
                if exists_el.text == 'Загрузить ещё':
                    download_more = browser.find_elements(By.CLASS_NAME, 'Button2-Content')
                    for i in download_more:
                        if i.text == 'Загрузить ещё':
                            i.click()
                            continue
            except StaleElementReferenceException:
                break
            except NoSuchElementException as e:
                logging.error(f'NoSuchElementException. Время ожидания истекло и возникла ошибка времени ожидания: {e}')
            except TimeoutException as e:
                logging.error(f'TimeoutError. Время ожидания истекло и возникла ошибка времени ожидания: {e}')
        tbody = browser.find_element(By.TAG_NAME, 'tbody')
        time.sleep(1)
        orders = tbody.find_elements(By.XPATH, "//tr[starts-with(@class, 'NativeTable_tr__')]")[:1]
        unpaid_o = []
        for tr in orders:
            time.sleep(1)
            td = tr.find_elements(By.TAG_NAME, 'td')

            if td[11].text == '0,00' and td[12].text == '0,00':
                unpaid_o.append([td[1].text, td[3].text, td[4].text, td[6].text])

        return 200, parse_id_driver_url, unpaid_o

    except TimeoutException:
        logging.error('TimeoutException. Время ожидания поиска элемента истекло!')
        return False
    except TimeoutError as ex:
        logging.error(f'TimeoutError. Время ожидания истекло и возникла ошибка времени ожидания: {ex}')
    except Exception as ex:
        logging.error(f'Exception. Ошибка {ex} {Exception}')
    except NoSuchElementException:
        return 'NoSuchElementException. Возможные проблемы c авторизацией по прямому запросу!'
    finally:
        browser.close()
        browser.quit()
