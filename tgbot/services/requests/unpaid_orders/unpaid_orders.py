import logging
import os

from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, \
    StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from tgbot.services.requests.general_requests import general_calendars
from tgbot.services.requests.settings_driver import add_cookies, options_driver

from dotenv import load_dotenv


load_dotenv()


def unpaid_orders_requests(phone, interval, url=None):
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
            tab_order = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Заказы')))
            tab_order.click()

        if interval is not None:
            # открыть календарь для установки периода
            general_calendars(wait, interval, browser)

        actions = ActionChains(browser)
        # устанавливаем фильтры для поиска нужных заказов
        filters = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Select__control')))
        for i in filters:
            if i.text == 'Статус':
                i.click()
                # выбор всех фильтров
                actions.send_keys([Keys.ENTER] * 8).perform()
                # закрытие окна выбора фильтров
                select_status = WebDriverWait(i, 30).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'Select__multi-value')))
                select_status.click()
                # удаление ненужных фильтров
                remove_filters_status = wait.until(
                    EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Select__multi-value__remove')))
                for rem_filter in remove_filters_status:
                    if rem_filter.get_dom_attribute('aria-label').strip('Remove ') != 'Выполнен':
                        rem_filter.click()
            elif i.text == 'Тип оплаты':
                i.click()
                # выбор всех фильтров
                actions.send_keys([Keys.ENTER] * 7).perform()
                # закрытие окна выбора фильтров
                select_status = WebDriverWait(i, 30).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'Select__multi-value')))
                select_status.click()
                # удаление ненужных фильтров
                remove_filters_payment = wait.until(
                    EC.visibility_of_all_elements_located((By.CLASS_NAME, 'Select__multi-value__remove')))
                for rem_filter in remove_filters_payment:
                    cashless = rem_filter.get_dom_attribute('aria-label').strip('Remove ')
                    if cashless not in ['Безналичные', 'Корп. счёт', 'Карта', 'Выполнен']:
                        rem_filter.click()

        # обработка пустого экрана заказов
        try:
            empty_order_sheet = WebDriverWait(browser, 5).until(
                EC.visibility_of_element_located((By.XPATH, "//h2[contains(text(), 'Пока ничего нет')]")))
            if empty_order_sheet.text == 'Пока ничего нет':
                status_requests['status'] = 200
                status_requests['unpaid_orders'] = []
                return status_requests
        except TimeoutException:
            pass

        # поиск неоплаченных заказов
        while True:
            try:
                # на каждой итерации проверяется элемент на странице
                exists_el = WebDriverWait(browser, 7).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Загрузить ещё')]")))
                if exists_el.is_enabled() is True:
                    # перебираются все кнопки для поиска 'Загрузить ещё'
                    download_more = wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, '#root > div.THUkpl > div > div.pEdyOl.vGEKNl > div > '
                                              'div.app-shell_layout__lb7na > div.Section_section__o33vD > main > '
                                              'div:nth-child(2) > div > div.Table_loadMore__hQyCq > button > span'))
                    )
                    for i in range(len(download_more)):
                        if download_more[i].text == 'Загрузить ещё':
                            # time.sleep(0.1)
                            browser.execute_script('arguments[0].click()', download_more[i])
                            # download_more[i].click()
            except StaleElementReferenceException:
                # обработка исключения и переход на новую итерацию
                continue
            except TimeoutException:
                # обработка исключения при отсутствии элемента на странице выше лимита из функции WebDriverWait
                break
        # сбор данных по неоплаченным заказам
        tbody = wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'tbody')))
        orders = WebDriverWait(tbody, 30).until(
            EC.visibility_of_all_elements_located(
                (By.XPATH, "//tr[starts-with(@class, 'NativeTable_tr__')]")))
        unpaid_orders = []
        for tr in orders:
            td = WebDriverWait(tr, 30).until(EC.visibility_of_all_elements_located((By.TAG_NAME, 'td')))
            if td[11].text == '0,00' and td[12].text == '0,00':
                unpaid_orders.append([td[1].text, td[3].text, td[4].text, td[6].text])

        status_requests['status'] = 200
        status_requests['unpaid_orders'] = unpaid_orders

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
