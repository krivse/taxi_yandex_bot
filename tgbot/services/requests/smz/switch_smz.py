import logging
import os
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from tgbot.services.requests.settings_driver import add_cookies, options_driver

from dotenv import load_dotenv


load_dotenv()


def switch_smz_request(phone=None, url=None):
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

        # проверка подключенной услуги
        try:
            WebDriverWait(browser, 3).until(EC.visibility_of_element_located(
                (By.XPATH, '//span[contains(text(), "Запрос водителю")]')))
            status_requests['status'] = 200
            status_requests['data'] = 'СМЗ не подключен, для подключения нужно обратиться в парк'
            return status_requests
        except TimeoutException:
            pass

        # поиск поля для переключения СМЗ
        find_switch_smz = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//div[starts-with(@class, "Group_formLayoutGroup__")]')))
        click_box = WebDriverWait(find_switch_smz[1], 30).until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "input.Checkbox-Control"))
        )
        print('find_switch_smz')
        time.sleep(0.5)
        # actions = ActionChains(browser)
        # actions.move_to_element(click_box[0]).click().perform()
        if click_box[0].is_selected():
            browser.execute_script('arguments[0].click()', click_box[0])
            status_requests['data'] = 'СМЗ выключен'
            print("Кнопка не выбрана", click_box[0].is_selected())

        elif not click_box[0].is_selected():
            browser.execute_script('arguments[0].click()', click_box[0])
            status_requests['data'] = 'СМЗ включен'
            print("Кнопка выбрана", click_box[0].is_selected())

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
