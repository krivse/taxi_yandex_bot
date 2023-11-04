import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


def general_calendars(wait, interval, browser):
    """Установка периода в календаре."""
    # открыть календарь
    actions = ActionChains(browser)
    popup_calendar = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//span[contains(@class, 'DateRangeInput_alignStart__')]")))
    popup_calendar.click()

    if int(interval.get('start_day')) < 8:
        # Проверяем переходящий день месяца в календаре
        click = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "body > div.Modal.Modal_visible.Modal_hasAnimation.Modal_size_m.Modal_view_default > "
                              "div.Modal-Wrapper > div > div > div > div > div.Datepicker_Box__2P_6f > "
                              "div:nth-child(2) > div.Header_Header__1cMVF > svg:nth-child(3)"))
        )
        actions.move_to_element(click).click(click).perform()

    calendars = wait.until(EC.visibility_of_all_elements_located(
        (By.XPATH, "//div[starts-with(@class, 'Calendar_Calendar__')]"))
    )

    for calendar in range(len(calendars)):
        # начальный месяц
        find_month = WebDriverWait(calendars[calendar], 30).until(
            EC.presence_of_element_located((By.TAG_NAME, 'span'))).text

        if find_month.startswith(interval.get('start_month')):
            # начальный день
            find_day = WebDriverWait(calendars[calendar], 30).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'span')))
            for day in find_day:
                if day.text == interval.get('start_day'):
                    day.click()
        # конечный месяц
        if find_month.startswith(interval.get('end_month')):
            # конечный день
            find_day = WebDriverWait(calendars[calendar], 30).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'span')))
            for day in find_day:
                if day.text == interval.get('end_day'):
                    day.click()

    # подтвердить даты в календаре
    confirm_date = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'Modal-Content')))
    click_button = WebDriverWait(confirm_date, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'Button2-Content')))
    click_button.click()
