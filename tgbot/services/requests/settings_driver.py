import logging
import os

from dotenv import load_dotenv

# from seleniumwire import webdriver
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import ChromiumOptions

from selenium.webdriver.support import expected_conditions as EC
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
    chrome_options.add_argument('--headless')
    # отключение автоматизированного управления браузером
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # игнорирование незащищенного соединения
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--no-check-certificate')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-audio')
    chrome_options.add_argument('--disable-3d-apis')
    chrome_options.add_argument('--disable-bookmark-autocomplete-provider')
    chrome_options.add_argument('--disable-bundled-ppapi-flash')
    chrome_options.add_argument('--disable-cloud-policy-service')
    chrome_options.add_argument('--disable-desktop-notifications')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-flash-stage3d')
    chrome_options.add_argument('--disable-full-history-sync')
    chrome_options.add_argument('--disable-improved-download-protection')

    chrome_options.add_argument('--disable-media-history')
    chrome_options.add_argument('--disable-media-source')
    chrome_options.add_argument('--disable-ntp-other-sessions-menu')
    chrome_options.add_argument('--disable-pepper-3d')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-print-preview')
    chrome_options.add_argument('--disable-restore-background-contents')
    chrome_options.add_argument('--disable-scripted-print-throttling')
    chrome_options.add_argument('--disable-smooth-scrolling')
    chrome_options.add_argument('--disable-speech-input')
    chrome_options.add_argument('--disable-web-media-player-ms')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-webaudio')
    chrome_options.add_argument('--disable-webgl')
    chrome_options.add_argument('--disable-xss-auditor')
    chrome_options.add_argument('--incognito')

    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-crash-reporter")
    chrome_options.add_argument("--disable-oopr-debug-crash-dump")
    chrome_options.add_argument("--no-crash-upload")
    chrome_options.add_argument("--disable-low-res-tiling")
    chrome_options.add_argument("--silent")

    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-web-resources")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--force-fieldtrials=SiteIsolationExtensions/Control")
    chrome_options.add_argument("--log-level=0")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--password-store=basic")
    chrome_options.add_argument("--test-type=webdriver")
    chrome_options.add_argument("--use-mock-keychain")

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
            ChromeDriverManager(version='114.0.5735.90').install(),
            chrome_options=chrome_options
        )

        return browser


def add_cookies(browser, wait):
    check_file = os.path.exists(f'{os.path.dirname(os.path.abspath(__file__))}/cookies')
    if check_file:
        for cookie in pickle.load(open(f'{os.path.dirname(os.path.abspath(__file__))}/cookies', 'rb')):
            cookie['domain'] = 'fleet.yandex.ru'
            browser.add_cookie(cookie)
    elif not check_file:
        return False
    browser.refresh()

    name_change_login = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'Button'))).text
    if name_change_login == 'Сменить логин':
        return False
    return browser
