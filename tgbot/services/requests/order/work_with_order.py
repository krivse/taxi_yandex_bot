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


def working_order_requests(phone, way, amount, url):
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
            search_driver.send_keys(Keys.BACK_SPACE)
            time.sleep(1)
            choice_driver = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'PNVeph')))
            choice_driver.click()

            # поиск вкладки "Заказы" и сохранение id водителя
            for_save_driver_url = wait.until(EC.presence_of_element_located((
                By.XPATH, "//a[starts-with(@href, '/drivers/')]"))).get_attribute('href')
            parse_id_driver_url = for_save_driver_url.split('/')[4]

        # поиск и переход на вкладку "Заказы"
        tab_order = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Заказы')))
        tab_order.click()

        # проверяем статус заказа, если статуса "Везёт клиента" нет, то он получает уведомление
        try:
            browser.implicitly_wait(2)
            order = browser.find_element(By.LINK_TEXT, 'Везёт клиента')
            order.click()
        except NoSuchElementException:
            empty_order = 'Нет заказов которые можно завершить'
            return None, None, None, None, None, None, empty_order

        # переключение между вкладками, влкадка завершения заказа
        new_window = browser.window_handles[1]
        browser.switch_to.window(new_window)

        number_order, description, address = None, [], None
        choose_mode = None
        price = []
        if way != 'cancel_confirm':
            if way == 'amount':
                # сбор информации заказа
                time.sleep(1)
                # номер заказа
                number_order = wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//span[starts-with(@class, 'Order_title__')]")
                )).text
                # описание заказа
                description = []
                rate_payment_method = wait.until(EC.visibility_of_all_elements_located(
                    (By.XPATH, "//dd[starts-with(@class, 'Sheet_value__')]")))
                for i in rate_payment_method:
                    description.append(i.text)
                # адрес заказа
                address = wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//span[starts-with(@class, 'OrderRoute_text__')]"))).text

            order = browser.find_element(
                By.XPATH, "//main/div[starts-with(@class, 'StatusSelector_container')]")
            order_complete = order.find_elements(By.CLASS_NAME, 'Button2-Content')[0]
            order_complete.click()

            browser.implicitly_wait(3)
            # завершение заказа по выбранному способу
            choose_mode = browser.find_element(By.CLASS_NAME, 'Modal-Content')

            if amount is True:
                amounts = browser.find_elements(By.CLASS_NAME, 'Radiobox-Text')
                for i in amounts:
                    price.append(i.text)

        # завершение заказа по фикс цене / таксомметру / отмена заказа
        if way == 'cancel_confirm':
            time.sleep(1)
            order = browser.find_element(
                By.XPATH, "//main/div[starts-with(@class, 'StatusSelector_container')]")
            order_cancel = order.find_elements(By.CLASS_NAME, 'Button2-Content')[-1]
            order_cancel.click()
            order = browser.find_element(
                By.XPATH, "//div[starts-with(@class, 'Dialog_buttons__')]")
            cancel_confirm = order.find_elements(By.CLASS_NAME, 'Button2-Content')[-1]
            cancel_confirm.click()
        elif way == 'taximeter':
            choose_complete = choose_mode.find_element(
                By.XPATH, f"//input[contains(@value, 'taximeter')]")
            choose_complete.click()
            time.sleep(1)
            accept_complete = choose_mode.find_element(
                By.XPATH, "//div[starts-with(@class, 'Dialog_buttons__')]"
            ).find_elements(
                By.CLASS_NAME, 'Button2-Content')[-1]
            accept_complete.click()
        elif way == 'fixed':
            time.sleep(1)
            accept_complete = choose_mode.find_element(
                By.XPATH, "//div[starts-with(@class, 'Dialog_buttons__')]"
            ).find_elements(
                By.CLASS_NAME, 'Button2-Content')[-1]
            accept_complete.click()

        return 200, parse_id_driver_url, price, number_order, description, address, None

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
