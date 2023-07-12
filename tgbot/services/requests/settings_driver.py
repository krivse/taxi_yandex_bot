import logging
import os
from dotenv import load_dotenv

# from seleniumwire import webdriver
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import ChromiumOptions
from selenium.webdriver.common.by import By

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
    # chrome_options.add_argument("--headless")
    # отключение автоматизированного управления браузером
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # игнорирование незащищенного соединения
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--no-check-certificate')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # установка user-agent
    chrome_options.add_argument(
        f'--user-agent={"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537"}')
    # отключаем webdriver
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # Создаем экземпляр браузера Chrome и передаем в него необходимые опции

    if os.getenv('USE_PROXY') is True:
        browser = webdriver.Chrome(
            ChromeDriverManager().install(),
            # seleniumwire_options=options,
            chrome_options=chrome_options
        )
        return browser

    elif not os.getenv('USE_PROXY') is False:
        browser = webdriver.Chrome(
            ChromeDriverManager().install(),
            chrome_options=chrome_options
        )
        return browser


def add_cookies(browser):
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
    return browser
