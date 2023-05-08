import logging
import os
import time
from dotenv import load_dotenv

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import ChromiumOptions
from selenium.common.exceptions import TimeoutException
import pickle


load_dotenv()

# тестовые url для определения опций и проверок
# url = 'https://ifconfig.co/'
# url = 'https://www.whatismybrowser.com/detect/what-is-my-user-agent/'
# url = 'https://2ip.ru/?ysclid=lgii8oi64t450760997'
# url = 'https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html'


# установка прокси
proxy = f'{os.getenv("PROXY_USER")}:{os.getenv("PROXY_PASS")}@{os.getenv("PROXY_HOST")}:{os.getenv("PROXY_PORT")}'
options = {
    'proxy': {
        'https': f'https://{proxy}',
    }
}


def options_driver():
    selenium_logger = logging.getLogger('seleniumwire')
    selenium_logger.setLevel(logging.ERROR)

    # user_agent = UserAgent().chrome
    chrome_options = ChromiumOptions()
    # передача необходимых опций в бразуер
    # открытие браузера в фоновом режиме эквивалентно chrome_options.headless = True
    chrome_options.add_argument("--headless")
    # отключение автоматизированного управления браузером
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # игнорирование незащищенного соединения
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--no-check-certificate')
    # установка user-agent
    chrome_options.add_argument(
        f'--user-agent={"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537"}')
    # отключаем webdriver
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # Создаем экземпляр браузера Chrome и передаем в него необходимые опции

    if os.getenv('USE_PROXY') is True:
        browser = webdriver.Chrome(
            ChromeDriverManager().install(),
            seleniumwire_options=options,
            options=chrome_options
        )
        return browser

    elif not os.getenv('USE_PROXY') is False:
        browser = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chrome_options
        )
        return browser


def authentication(queue, pass_park):
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


def taxi_ya_park(phone, limit):
    browser = options_driver()
    wait = WebDriverWait(browser, 30)

    # Указываем URL-адрес для входа в систему
    current_park = 'https://fleet.yandex.ru/drivers?status=working&park_id=bb83932233b3484089a65d301e6aea08'

    try:
        browser.get(current_park)

        check_file = os.path.exists(f'{os.path.dirname(os.path.abspath(__file__))}/cookies')
        if check_file:
            browser.implicitly_wait(30)
            for cookie in pickle.load(open(f'{os.path.dirname(os.path.abspath(__file__))}/cookies', 'rb')):
                browser.add_cookie(cookie)
        elif not check_file:
            return False

        browser.refresh()

        name_change_login = browser.find_element(by=By.CLASS_NAME, value='Button2-Content').text
        if name_change_login == 'Сменить логин':
            return False

        # выбор парка
        # choice_park = browser.find_element(by=By.CLASS_NAME, value='ParkButton_container__ALtGi')
        # choice_park.click()

        # поиск водителя
        search_driver = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'Textinput-Control')))
        search_driver.send_keys(phone)
        time.sleep(1)
        choice_driver = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'PNVeph')))
        choice_driver.click()
        change_limit = wait.until(EC.element_to_be_clickable((By.NAME, 'accounts.balance_limit')))
        change_limit.clear()
        # очистить поле
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
