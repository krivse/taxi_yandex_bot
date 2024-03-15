import logging
import os

from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from tgbot.services.requests.settings_driver import add_cookies, options_driver

from dotenv import load_dotenv


load_dotenv()


def working_order_requests(phone, way, amount, url=None):
    browser = options_driver()
    wait = WebDriverWait(browser, 30)

    if url is None:
        current_park = f'https://fleet.yandex.ru/contractors?status=working&park_id={os.getenv("X_Park_ID")}'
    else:
        current_park = f'https://fleet.yandex.ru/contractors/{url}/orders?park_id={os.getenv("X_Park_ID")}'

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

            # поиск и переход на вкладку "Заказы"
            tab_order = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//span[contains(text(), 'Заказы')]")))
            tab_order.click()

        # проверяем статус заказа, если статуса "Везёт клиента" нет, то он получает уведомление
        try:
            order = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.LINK_TEXT, 'Везёт клиента')))
            order.click()
        except TimeoutException:
            status_requests['empty_order'] = 'Нет заказов, которые можно отменить'
            return status_requests

        # переключение между вкладками, влкадка завершения заказа
        new_window = browser.window_handles[1]
        browser.switch_to.window(new_window)
        if way != 'cancel_confirm':
            # сбор информации о заказе
            if way == 'amount':
                # номер заказа
                number_order = wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//span[starts-with(@class, 'Order_title__')]")
                )).text
                status_requests['number_order'] = number_order

                # описание заказа
                description = []
                rate_payment_method = wait.until(EC.visibility_of_all_elements_located(
                    (By.XPATH, "//dd[starts-with(@class, 'Sheet_value__')]")))
                for i in rate_payment_method:
                    description.append(i.text)
                status_requests['description'] = description

                # адрес заказа
                address = wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//span[starts-with(@class, 'OrderRoute_text__')]"))).text
                status_requests['address'] = address

            # кнопка завершения заказа
            order_completion_button = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//main/div[starts-with(@class, 'StatusSelector_container')]")))
            # клик на кнопку завершения заказа
            click_on_buttons = WebDriverWait(order_completion_button, 30).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'Button2-Content')))
            click_on_buttons.click()

            # сбор информации стоимости заказа фикс цене / таксометру
            price = []
            if amount is True:
                amounts = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Radiobox-Text')))
                for i in amounts:
                    price.append(i.text)
            status_requests['price'] = price

        # завершение заказа по фикс цене / таксометру / отмена заказа
        # отмена заказа
        if way == 'cancel_confirm':
            order_cancel_button = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//main/div[starts-with(@class, 'StatusSelector_container')]")))
            click_on_buttons = WebDriverWait(order_cancel_button, 30).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Button2-Content')))[-1]
            click_on_buttons.click()
            order_cancel_too = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[starts-with(@class, 'Dialog_buttons__')]")))
            cancel_confirm = WebDriverWait(order_cancel_too, 30).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Button2-Content')))[-1]
            cancel_confirm.click()
            status_requests['status'] = 200
        # завершение заказа по таксометру
        elif way == 'taximeter':
            choose_mode = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Modal-Content')))
            choose_complete = WebDriverWait(choose_mode, 30).until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@value, 'taximeter')]")))
            choose_complete.click()

            accept_complete = WebDriverWait(choose_mode, 30).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[starts-with(@class, 'Dialog_buttons__')]")))
            click_on_buttons = WebDriverWait(accept_complete, 30).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Button2-Content')))[-1]
            click_on_buttons.click()
            status_requests['status'] = 200
        # завершение заказа по фикс цене
        elif way == 'fixed':
            choose_mode = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Modal-Content')))
            accept_complete = WebDriverWait(choose_mode, 30).until(EC.visibility_of_element_located(
                (By.XPATH, "//div[starts-with(@class, 'Dialog_buttons__')]")))
            click_on_buttons = WebDriverWait(accept_complete, 30).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Button2-Content')))[-1]
            click_on_buttons.click()
            status_requests['status'] = 200

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
