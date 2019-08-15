from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time
import re
import html
import json
import os
import threading


def base():
    url = 'https://mp.weixin.qq.com/mp/getmasssendmsg?__biz=MzAxNTg3OTUzMw==&uin=MzA1MjIwMjk0NA%3D%3D&key=05eee5e78663c69d3a102ccf98991b55fcbf68e0b44817ab728c29d200247c40635515831fbb677866bcc696e5c006a43efb9693e99fd2988c2d8bf5a80635b6e6c67ca03358a460f61a1a8475ce84e5&devicetype=Windows+10&version=62060833&lang=zh_CN&ascene=7&pass_ticket=G018ZWS%2BXDDH9kF0edvNYSWFDHFJavA2fWohH%2F3AoIo3sp%2Bq2KxXPccnMhVGzrFh'
    check_url = 'https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzAxNTg3OTUzMw==&scene=124&#wechat_redirect'
    opt = webdriver.ChromeOptions()
    browser = webdriver.Chrome(options=opt)
    wait = WebDriverWait(browser, 20)
    browser.get(url)
    now = time.time()
    while True:
        browser.refresh()
        time.sleep(5)
        try:
            wait.until(EC.presence_of_element_located((By.ID, 'nickname')))
            print('cookies生效中')
            print(browser.get_cookies())
        except:
            print('cookies失效')
            break
        finally:
            print(time.time() - now)


class WeChat:
    def __init__(self, data_list):
        self.opt = webdriver.ChromeOptions()
        self.opt.add_argument('--headless')
        self.browser = webdriver.Chrome(options=self.opt)
        self.wait = WebDriverWait(self.browser, 20)
        self.data_list = data_list
        self.save_dir = r'C:\Users\17337\houszhou\data\SpiderData\微信公众号\data\test'
        self._is_alive = True

    def kill(self):
        self._is_alive = False

    def start(self):
        th = threading.Thread(target=self.keep_alive)
        th.start()

    def keep_alive(self):
        now = time.time()
        data = self.data_list[0]
        url = data.get('url')
        name = data.get('name')
        self.get(url, name)
        print(time.time() - now)
        time.sleep(3)
        while self._is_alive:
            self.browser.refresh()
            time.sleep(5)
            if self.result():
                self.home(self.browser.page_source, name)
            else:
                print('cookies失效')
                self._is_alive = False
            print(time.time() - now)
            time.sleep(2 * 60)
        self.browser.quit()

    def get(self, url, name):
        self.browser.get(url)
        if self.result():
            self.home(self.browser.page_source, name)
        else:
            print('cookies失效')
            self._is_alive = False

    def result(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, 'nickname')))
            return True
        except:
            return False

    def home(self, response, name):
        msg = re.findall('var msgList = \'({.*?})\';', response)
        msg = html.unescape(msg[0])
        msg = json.loads(msg)
        save_data = {'name': name, 'list': []}
        for item in msg.get('list')[:10]:
            comm_msg_info = item.get('comm_msg_info')
            app_msg_ext_info = item.get('app_msg_ext_info')
            datetime = comm_msg_info.get('datetime')
            title = app_msg_ext_info.get('title')
            digest = app_msg_ext_info.get('digest')
            content_url = app_msg_ext_info.get('content_url')
            data = {'datetime': datetime, 'title': title, 'digest': digest, 'content_url': content_url}
            save_data['list'].append(data)
        file_path = os.path.join(self.save_dir, '{}.json'.format(name))
        with open(file_path, 'w', encoding='utf8')as f:
            print('save', save_data)
            f.write(json.dumps(save_data, ensure_ascii=False))


if __name__ == '__main__':
    demo = [{'fakeid': 'MjM5MjE5MjA0MA==', 'name': '深圳之窗',
             'url': 'https://mp.weixin.qq.com/mp/getmasssendmsg?__biz=MjM5MjE5MjA0MA==&uin=MzA1MjIwMjk0NA%3D%3D&key=6a52e6304f29e3a771fdea64e981e0b13dc86f071965f9f43e0e73f7d2f9c85f03663a42655cbec3c82fbcb1b294bec81e45b4cecb04e6e72c6a355b44700ff4e8fed6f1e92ee958cbc3b5c224f3e233&devicetype=Windows+10&version=62060833&lang=zh_CN&ascene=7&pass_ticket=G%2BCIDaFmcM1PekS0HpX69oL3UdTy5%2B2nkpGOXdGWl7mlTO5SiZGvrn49fhKci3kw'}]
    wc = WeChat(demo)
    wc.start()
    # time.sleep(20)
    # wc.kill()
