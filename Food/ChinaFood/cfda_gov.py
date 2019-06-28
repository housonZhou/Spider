import requests
import time
import json
import os
import re
import threading
import traceback
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Crawl(object):
    def __init__(self):
        self.retry = 20  # 单个请求重试次数
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
        self._base_url = 'http://samr.cfda.gov.cn/WS01/CL1688/index_416.html'  # 用于验证cookies有效性的链接
        self._cookies = {}
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')
        self._driver = webdriver.Chrome(chrome_options=self.chrome_options)
        self.watch = True  # 是否验证cookies，用于爬虫结束时关闭线程
        threading.Thread(target=self.watch_cookies).start()  # 开启线程持续验证cookie是否失效

    def get_new_cookies(self):  # 用selenium获取新cookies
        print('get cookies')
        self._driver.delete_all_cookies()
        self._driver.get(self._base_url)
        for item in self._driver.get_cookies():
            self._cookies[item.get('name')] = item.get('value')

    def over_watch(self):  # 停止验证cookies
        self.watch = False

    def watch_cookies(self):  # 持续验证cookie是否失效，获取新cookies
        while self.watch:
            response = requests.get(self._base_url, headers=self.headers, cookies=self._cookies)
            if response.status_code != 200:
                self.get_new_cookies()
        print('watch over')

    def set_cookies(self, new_cookie):  # 设置cookies
        self._cookies = new_cookie

    def get(self, url):
        retry = self.retry
        response = requests.get(url, headers=self.headers, cookies=self._cookies)
        while response.status_code != 200:
            retry -= 1
            if retry < 0:  # 单个请求重试超过规定次数则返回空数据
                return ''
            print('sleep')
            time.sleep(0.5)  # 请求失败休眠0.5秒，等待cookies更新
            response = requests.get(url, headers=self.headers, cookies=self._cookies)
        return response


def get_json(json_path):
    with open(json_path, 'r', encoding='utf8')as f:
        for line in f:
            yield json.loads(line.strip())


def start(start_list, need_list, save_dir, qp):
    for item in start_list:
        name = item.get('name')
        for pro_name in need_list:
            if pro_name in name:
                item['save_dir'] = os.path.join(save_dir, pro_name)
                qp.put(item)


def consumer_download(qp):
    while not qp.empty():
        item = qp.get()
        url = item.get('url')
        file_name = item.get('name')
        base_path = item.get('save_dir')
        try:
            print('正在下载文件 ', url, file_name)
            down_file(url, file_name, base_path)
        except:
            print('文件下载失败： {}'.format(url))
            traceback.print_exc()
    cl.over_watch()


def down_file(url, file_name, save_dir):
    file_name = re.sub('[\\\/\:\*\?\"\<\>\→]', '_', file_name)  # 更改无法保存的字符
    new_name = os.path.join(save_dir, file_name)
    if os.path.exists(new_name):  # 若文件存在则跳过不下载
        print('文件已存在')
        return
    try:
        data = cl.get(url)
        if data:
            with open(new_name, 'wb')as f:
                f.write(data.content)
        else:
            print('无法获取数据： {}'.format(url, file_name))
    except:
        print("文件下载失败： url:{}".format(url))
        traceback.print_exc()


if __name__ == '__main__':
    th_num = 4  # 线程数量
    need_list = ['北京']  # 要下载的地区，支持多地区下载 ['', '', '', ...]
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\china\0626_1810'  # 保存的文件夹路劲
    save_json = r'C:\Users\17337\houszhou\data\SpiderData\Food\china\0626_0941.json'
    start_list = get_json(save_json)  # 读取json文件
    q_link = Queue()
    for name in need_list:
        if not os.path.exists(os.path.join(save_dir, name)):  # 如果文件夹不存在则创建
            os.mkdir(os.path.join(save_dir, name))
    start(start_list, need_list, save_dir, q_link)  # 待下载的数据压入队列
    cl = Crawl()
    for _ in range(th_num):  # 开启4条线程同时下载数据
        th = threading.Thread(target=consumer_download, args=(q_link,))
        th.start()
