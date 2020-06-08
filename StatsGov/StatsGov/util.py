import time

from selenium import webdriver
from selenium.webdriver import ChromeOptions


option = ChromeOptions()
option.add_experimental_option('excludeSwitches', ['enable-automation'])


def get_cookie(url):
    driver = webdriver.Chrome(options=option)
    driver.get(url)
    time.sleep(3)
    cookies = driver.get_cookies()
    print('cookies: ', cookies)
    driver.quit()
    items = []
    dict_ = {}
    for i in range(len(cookies)):
        cookie_value = cookies[i]
        item = cookie_value['name'] + '=' + cookie_value['value']
        items.append(item)
        dict_[cookie_value['name']] = cookie_value['value']
    # cookiestr = '; '.join(a for a in items)
    # print(cookiestr)
    # return cookiestr
    return dict_
