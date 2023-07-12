import re


def phone_formatting(user_phone):
    """Форматирование телеофона 79999999999."""
    return int(re.sub(r'[+() -]', '', user_phone).replace(user_phone[0], '7', 1))
