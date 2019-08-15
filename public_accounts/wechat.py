import requests
import re
import os
import json
import time
import math
import traceback
from lxml.etree import HTML
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from public_accounts.setting import SAVE_DIR, LOG_DIR, SEARCH_LIST, COOKIES, TOKEN, SLEEP_TIME, ACCOUNT, PASSWORD
from requests.packages.urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class WeChatSpider:
    def __init__(self, info_msg):
        """
        初始化，创建新文件夹存放数据
        :param info_msg: {'fakeid': 'MjM5MjE5MjA0MA==', 'name': '深圳之窗'}
        """
        self.cookies = {}
        self.token = ''
        self.name = info_msg.get('name')
        self.fake_id = info_msg.get('fakeid')  # 公众号唯一id，需提前获知
        self.url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?token={token}&lang=zh_CN&f=json&ajax=1&' \
                   'random=0.8290188508387306&action=list_ex&begin={begin}&count=5&query={flag}&fakeid={id}&type=9'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/75.0.3770.142 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&'
                       'token=36320133&lang=zh_CN',
        }
        self._mk()

    def _mk(self):
        now = time.time()
        now_mark = time.strftime("%Y-%m-%d_%H-%M", time.localtime(now))
        self._save_dir = os.path.join(SAVE_DIR, now_mark)
        self._log_dir = os.path.join(LOG_DIR, now_mark)
        if not os.path.exists(self._save_dir):
            os.mkdir(self._save_dir)
        if not os.path.exists(self._log_dir):
            os.mkdir(self._log_dir)
        self.save_path = os.path.join(self._save_dir, '{}.json'.format(self.name))
        self.fail_path = os.path.join(self._log_dir, '{}-error.json'.format(self.name))
        self.file = open(self.save_path, 'w', encoding='utf8')
        self.fail = open(self.fail_path, 'w', encoding='utf8')

    def __del__(self):
        self.file.close()
        self.fail.close()

    def _write(self, file, write_data):
        """保存json数据"""
        file.write(json.dumps(write_data, ensure_ascii=False) + '\n')
        file.flush()

    def run(self):
        """
        查询公众号,循环抓取所有文章
        """
        all_count = self.main(flag='*').get('all')
        if all_count > 10:
            page = math.floor(all_count / 10)
            if page > 199:  # 不超过200页
                page = 199
            for i in range(page):
                time.sleep(SLEEP_TIME)
                print('name: {}, index: {}, all: {}'.format(self.name, i + 1, page))
                self.main(begin=(i + 1) * 10, flag='*')
        elif all_count == 0:
            error_data = {'data': {'name': self.name, 'fakeid': self.fake_id, 'all': all_count},
                          'error': '公众号数据过少', 'msg': 'run error'}
            print('error: ', error_data)
            self._write(self.fail, error_data)

    def top_ten(self):
        """抓取公众号前10篇文章"""
        all_count = 0
        this_count = self.main().get('this')
        i = 0
        all_count += this_count
        while all_count < 10:
            i += 1
            if i > 10:
                break
            time.sleep(SLEEP_TIME)
            this_count = self.main(begin=i * 5).get('this')
            all_count += this_count
        print('{}共抓取: {}条数据'.format(self.name, all_count))

    def main(self, begin=0, retry=10, flag=''):
        """
        查询公众号文章,并保存数据
        :param begin: 查询起点
        :param retry: 重试次数
        :param flag: ''为按时间顺序搜索文章，'*'为搜索所有文章（但时间顺序不保证）
        :return: 公众号文章总数
        """
        url = self.url.format(begin=begin, id=self.fake_id, token=self.token, flag=flag)
        try:
            response = self.get(url)
            data = self.list_detail(response, url)
            if data.get('all') > 0:
                return data
            elif retry > 0:
                if data.get('msg', '') == '操作频繁':
                    print('操作频繁,休眠{}秒重试'.format(SLEEP_TIME))
                    time.sleep(SLEEP_TIME)
                elif data.get('msg', '') == 'cookies失效':
                    self.update_cookies()
                return self.main(begin=begin, retry=retry - 1, flag=flag)
            else:
                return {'all': 0, 'this': 0, 'code': -2, 'msg': '重试过多'}
        except:
            error_data = {'data': url, 'error': str(traceback.print_exc()), 'msg': 'main error'}
            print('error: ', error_data)
            self._write(self.fail, error_data)
            return {'all': 0, 'this': 0}

    def update_cookies(self):
        print('正在重新登陆，更新cookies')
        wl = WeChatLogin()
        login_data = wl.login()
        self.set_config(login_data)

    def get(self, url, **kwargs):
        response = requests.get(url, headers=self.headers, cookies=self.cookies, verify=False, **kwargs)
        return response.content.decode()

    def list_detail(self, response, url):
        """
        通过接口查询到文章链接,发送请求抓取文章内容
        :param response: 接口返回数据
        :param url: 接口链接
        :return: 公众号文章总数
        """
        response = json.loads(response)
        data_list = response.get('app_msg_list', '')
        if not data_list:
            error_data = {'data': response, 'error': '接口数据异常', 'msg': url}
            print('response no data: ', response)
            self._write(self.fail, error_data)
            if response.get('base_resp'):
                err_msg = response.get('base_resp').get('err_msg')
                if err_msg == 'invalid session' or err_msg == 'invalid csrf token':
                    return {'all': 0, 'this': 0, 'code': -1, 'msg': 'cookies失效'}
            else:
                return {'all': 0, 'this': 0, 'code': -1, 'msg': '操作频繁'}
        else:
            for item in data_list:
                try:
                    self.save_page(item)
                except:
                    error_data = {'data': item, 'error': str(traceback.print_exc()), 'msg': 'item error'}
                    print('error: ', error_data)
                    self._write(self.fail, error_data)
        count = response.get('app_msg_cnt', 0)
        print(count)
        return {'all': count, 'this': len(data_list), 'code': 0, 'msg': 'OK'}

    def save_page(self, item):
        """
        保存单条文章页面信息
        :param item: 单条接口数据
        :return:
        """
        aid = item.get('aid')
        title = item.get('title')
        page_url = item.get('link')
        digest = item.get('digest')  # 摘要
        create_time = self.change_time(item.get('create_time', ''))
        update_time = self.change_time(item.get('update_time', ''))
        content = self.page_content(page_url)  # 文本内容
        if not content:
            error_data = {'data': page_url, 'error': 'page not content data', 'msg': 'page error'}
            self._write(self.fail, error_data)
        save_data = {'aid': aid, 'title': title, 'url': page_url, 'digest': digest, 'create_time': create_time,
                     'update_time': update_time, 'content': content}
        print('save: ', save_data)
        self._write(self.file, save_data)

    def page_content(self, url):
        page_data = self.get(url)
        return self._content(page_data)

    def _content(self, response):
        tree = HTML(response)
        content = tree.xpath('string(//div[@class="rich_media_content "])')
        return content.strip() if content else ''

    def change_time(self, time_stamp):
        if not time_stamp:
            return ''
        time_array = time.localtime(time_stamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)

    def set_config(self, conf):
        self.cookies = conf.get('cookies')
        self.token = conf.get('token')

    def get_config(self):
        return {'cookies': self.cookies, 'token': self.token}

    def test(self):
        print(self.name)
        print(self.main(0))


class WeChatLogin:
    def __init__(self):
        self.url = 'https://mp.weixin.qq.com/'
        self.account = ACCOUNT
        self.password = PASSWORD
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.png = r'C:\Users\17337\houszhou\data\SpiderData\微信公众号\登陆二维码.png'

    def login(self):
        """
        须提供微信公众号账号密码登陆，并根据提示用手机扫码完成登陆
        :return: 登陆后的cookies和token
        """
        self.browser.get(self.url)
        email = self.wait.until(EC.presence_of_element_located((By.NAME, 'account')))
        email.send_keys(self.account)
        time.sleep(0.5)
        password = self.wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        password.send_keys(self.password)
        time.sleep(0.5)
        btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn_login')))
        btn.click()
        while True:
            token = re.findall('token=(\d+)', self.browser.current_url)
            if token:
                break
            else:
                print('请扫描二维码登陆')
                time.sleep(5)
        return {'cookies': {i.get('name'): i.get('value') for i in self.browser.get_cookies()}, 'token': token[0]}

    def __del__(self):
        self.browser.quit()


if __name__ == '__main__':
    # lg = WeChatLogin()
    # data = lg.login()
    # print(data)
    info = {'cookies': COOKIES, 'token': TOKEN}
    for msg in SEARCH_LIST:
        wc = WeChatSpider(msg)
        wc.set_config(info)
        wc.top_ten()
        info = wc.get_config()
        time.sleep(SLEEP_TIME)
