import json
import time
import requests
from lxml.etree import HTML
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from public_accounts.GsData.request.setting import LINK_LIST, SAVE_PATH, SLEEP_TIME, ACCOUNT, PASSWORD, COOKIES_PATH
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def base_req(url, method='GET', **kwargs):
    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
    }
    if kwargs.get('headers', {}):
        kwargs.get('headers').update(base_headers)
    s = requests.Session()
    s.keep_alive = False
    return s.request(method, url, verify=False, **kwargs)


def get(url, **kwargs):
    return base_req(url, method='GET', **kwargs)


def page_one(url):
    req_data = get(url).content.decode()
    return _content(req_data)


def _content(response):
    tree = HTML(response)
    content = tree.xpath('string(//div[@class="rich_media_content "])')
    return content.strip() if content else ''


class QBO:
    def __init__(self):
        self._cookies = {}
        self.url = 'http://www.gsdata.cn/rank/toparc?wxname={}&wx={}&sort=-1'
        self.headers = {'X-Requested-With': 'XMLHttpRequest'}
        self.file = open(SAVE_PATH, 'w', encoding='utf8')
        self.cookies_path = COOKIES_PATH
        self.set_cookies()

    def __del__(self):
        self.file.close()

    def set_cookies(self):
        with open(self.cookies_path, 'r', encoding='utf8')as f:
            self._cookies = json.load(f)
            print('set cookies: ', self._cookies)

    def get_cookies(self):
        return self._cookies

    def save_cookies(self):
        with open(self.cookies_path, 'w', encoding='utf8')as f:
            json.dump(self._cookies, f)

    def top_ten(self):
        for item in LINK_LIST:
            name = item.get('wxname')
            wx = item.get('wx')
            url = self.url.format(name, wx)
            print(name, url)
            data = self.post(url)
            if data:
                self.page_detail(data)
            else:
                print('无任何数据: ', url)
            # post_data = json.loads(data.content.decode())
            time.sleep(SLEEP_TIME)

    def post(self, url, retry=10, **kwargs):
        if retry < 0:
            return
        try:
            req_data = base_req(url, method='POST', headers=self.headers, cookies=self._cookies, **kwargs)
            if req_data.status_code == 200 and req_data.content.decode().strip():
                return req_data.content.decode().strip()
            else:
                print('cookies失效')
                self.update_cookies()
                return self.post(url, retry=retry - 1, **kwargs)
        except Exception as e:
            print('post error: ', e)
            return self.post(url, retry=retry - 1, **kwargs)

    def update_cookies(self):
        qd = QBDriver()
        cookies = qd.login()
        if cookies:
            self._cookies = cookies
            self.save_cookies()
            print('更新cookies成功')
        else:
            print('更新cookies失败')

    def page_detail(self, page_data: str):
        data = json.loads(page_data).get('data')
        if not data:
            print('no data', page_data)
            return
        for item in data:
            try:
                title = item.get('title')
                url = item.get('url')
                time_map = item.get('posttime')
                name = item.get('name')
                content = page_one(url)
                save_data = {'name': name, 'title': title, 'url': url, 'time_map': time_map, 'content': content}
                print(save_data)
                self._write(save_data)
            except Exception as e:
                print(e)

    def _write(self, save_data):
        self.file.write(json.dumps(save_data, ensure_ascii=False) + '\n')
        self.file.flush()


class QBDriver:
    def __init__(self):
        self.url = 'https://u.gsdata.cn/member/login'
        self.account = ACCOUNT
        self.password = PASSWORD
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)

    def login(self) -> dict:
        """
        须提供清博数据账号密码登陆
        :return: 登陆后的cookies
        """
        self.browser.get(self.url)
        to_login = self.wait.until(EC.presence_of_element_located((By.XPATH,
                                                                   '//div[@class="loginModal-header clearfix"]/a[2]')))
        to_login.click()
        email = self.wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        email.send_keys(self.account)
        time.sleep(0.5)
        password = self.wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        password.send_keys(self.password)
        time.sleep(0.5)
        remember = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'check-loginIcons')))
        remember.click()
        time.sleep(0.5)
        btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'loginform-btn')))
        btn.click()
        i = 20
        while i > 0:
            if self.browser.current_url == 'https://u.gsdata.cn/user/index':
                print('登录成功')
                return {i.get('name'): i.get('value') for i in self.browser.get_cookies()}
            else:
                print('登陆未生效')
                time.sleep(5)
                i -= 1
        return {}

    def __del__(self):
        self.browser.close()


if __name__ == '__main__':
    qb = QBO()
    qb.top_ten()
