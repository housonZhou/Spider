import os
import re
import lxml
import time
import random
import requests
import traceback
from lxml import etree
from selenium import webdriver
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def retry_get(url, data=None):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    if data:
        headers.update(data)
    s = requests.session()
    s.keep_alive = False
    time.sleep(random.random())
    req = s.get(url, headers=headers, verify=False)
    return req


def base_req(url, type='get', data=None):
    num = 5
    while num > 0:
        if type == 'get':
            req_data = retry_get(url, data=data)
        else:
            req_data = ""
        if req_data.status_code < 400:
            return req_data
        else:
            num -= 1
    return ""


def load_html(req):
    req_data = req.content.decode()
    return lxml.etree.HTML(req_data)


def get_page_url(html_tree, time_map):
    odd_list = html_tree.xpath('//td[@class="ListColumnClass15"]')
    data = []
    for item in odd_list:
        try:
            link = item.xpath('a/@href')[0]
            link_time = item.xpath('string(span)')
            link_time = re.findall('\d{4}\-\d{2}\-\d{2}', link_time)[0]
            if link_time > time_map:
                data.append({'page_url': "http://samr.cfda.gov.cn/WS01{}".format(link[2:]), 'page_time': link_time})
        except:
            print("解析列表页面出错：")
            traceback.print_exc()
    return data


def page_detail(url, page_tree, link_time):
    data_list = []
    try:
        need_type = ['xlsx', 'xls', 'csv']
        a_link_list = page_tree.xpath('//a[starts-with(@href,"/directory/web/WS01/images")]')
        page_title = page_tree.xpath('string(//td[@class="articletitle3"])').strip()
        if '食品' not in page_title:
            return []
        for link_item in a_link_list:
            try:
                link = link_item.xpath('@href')[0]
                file_name = link_item.xpath('string(.)')
                link_type = link.split('.')[-1]
                if (link_type not in need_type) or ('合格' not in file_name):
                    continue
                tag = '_不合格信息_' if '不合格' in file_name else '_合格信息_'
                down_name = "{}{}{}@{}.{}".format(page_title, file_name, tag, link_time, link_type)
                data_list.append({'url': 'http://samr.cfda.gov.cn{}'.format(link), 'name': down_name,
                                  'page_url': url, 'page_title': page_title})
            except:
                print("解析下载文件错误：{}".format(url))
                traceback.print_exc()
    except:
        print("解析目标详情页面错误：{}".format(url))
        traceback.print_exc()
    return data_list


def down_file(url, file_name, save_dir):
    old_name = os.path.join(save_dir, url.split('/')[-1])
    new_name = os.path.join(save_dir, file_name)
    if os.path.exists(new_name):
        print('文件已存在')
        return
    options = webdriver.ChromeOptions()
    prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': save_dir}
    options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(chrome_options=options)
    try:
        print(url)
        driver.get(url)
        time.sleep(8)
        os.rename(old_name, new_name)
        driver.quit()
    except:
        print("文件下载失败： url:{}".format(url))
        traceback.print_exc()


def demo():
    # cl = Crawl()
    # url = "http://samr.cfda.gov.cn/WS01/CL1664/index_2.html"
    # cl = Crawl()
    # cl.get(url)
    # page_data = cl.page_source()
    # data_html = lxml.etree.HTML(page_data)
    # a = get_page_url(data_html, "")
    # print(a)
    # print(len(a))

    # url = "http://samr.cfda.gov.cn/WS01/CL1688/241824.html"
    # cl.get(url)
    # data = page_detail(url, cl.page_tree(), "")
    # print(data)

    url = "http://samr.cfda.gov.cn/directory/web/WS01/images/localgov/gov_1553807264022.xlsx"
    # cl.get(url)
    # time.sleep(10)
    # down_file(url, r"C:\Users\17337\houszhou\data\SpiderData\Food\china")
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\test'
    data_list = []
    for item in data_list:
        url = item.get('url')
        name = item.get('name')
        down_file(url, name, save_dir)


class Crawl(object):
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')
        self._driver = webdriver.Chrome(chrome_options=self.chrome_options)

    def get(self, url):
        self._driver.get(url)

    def page_source(self):
        return self._driver.page_source

    def page_tree(self):
        return lxml.etree.HTML(self._driver.page_source)

    def wait_for(self, url):
        self._driver.get(url)
        wait = WebDriverWait(self._driver, 15)
        in_put = wait.until(EC.presence_of_all_elements_located)
        return in_put

    def driver(self):
        return self._driver


if __name__ == '__main__':
    demo()
