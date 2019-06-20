import requests
import os
import re
import lxml
import time
import random
import traceback
from lxml import etree
from fake_useragent import UserAgent


def retry_get(url):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    s = requests.session()
    s.keep_alive = False
    time.sleep(random.random())
    req = s.get(url, headers=headers, verify=False)
    return req


def retry_post(url, post_data):
    ua = UserAgent()
    page_num = post_data.get('page_num')
    headers = {"User-Agent": ua.random}
    data = {
        "infotypeId": "",
        "jdid": "3",
        "area": "014501068",
        "divid": "div435",
        "vc_title": "",
        "vc_number": "",
        "sortfield": "compaltedate:0",
        "currpage": "{}".format(page_num),
        "vc_filenumber": "",
        "vc_all": "抽检",
        "texttype": "0",
        "fbtime": "-1",
        "fields": "",
        "fieldConfigId": "",
        "hasNoPages": "",
        "infoCount": ""
    }
    s = requests.session()
    s.keep_alive = False
    re_data = s.post(url, data=data, headers=headers)
    return re_data


def base_req(url, type='get', post_data={}):
    num = 5
    while num > 0:
        if type == 'get':
            data = retry_get(url)
        else:
            data = retry_post(url, post_data)
        if data.status_code < 400:
            return data
        else:
            num -= 1
    return ""


def load_html(req):
    req_data = req.content.decode()
    return lxml.etree.HTML(req_data)


def get_page_url(html_tree, time_map):
    odd_list = html_tree.xpath('//tr[@class="tr_main_value_odd"]')
    even_list = html_tree.xpath('//tr[@class="tr_main_value_even"]')
    data = []
    for item in odd_list + even_list:
        link = item.xpath('td[2]/a/@href')[0]
        link_time = item.xpath('td[3]/text()')[0]
        link_time = link_time.strip()
        if link_time > time_map:
            data.append({'page_url': link, 'page_time': link_time})
    return data


def page_detail(url, link_time):
    data_list = []
    try:
        need_type = ['xlsx', 'xls', 'csv']
        page_data = base_req(url)
        page_tree = load_html(page_data)
        a_link_list = page_tree.xpath('//a[starts-with(@href,"/module/download/")]')
        page_title = page_tree.xpath('string(//p[@class="sp_title con-title"])')
        # print(len(a_link_list))
        # print("page_title", page_title)
        if '食品' not in page_title:
            return []
        for link_item in a_link_list:
            try:
                link = link_item.xpath('@href')[0]
                file_name = link_item.xpath('string(.)')
                print(link, file_name)
                link_type = link.split('.')[-1]
                if (link_type not in need_type) or ('合格' not in file_name):
                    continue
                down_name = "{}{}@{}.{}".format(page_title, file_name, link_time, link_type)
                data_list.append({'url': 'http://www.jiangxi.gov.cn{}'.format(link), 'name': down_name,
                                  'page_url': url, 'page_title': page_title})
            except:
                print("解析下载文件错误：{}".format(url))
                traceback.print_exc()
    except:
        print("解析目标详情页面错误：{}".format(url))
        traceback.print_exc()
    return data_list


def down_file(url, save_dir, file_name):
    with open(os.path.join(save_dir, "{}".format(file_name)), 'wb')as f:
        file_data = base_req(url)
        if file_data:
            f.write(file_data.content)
            print("文件下载成功")
        else:
            print("下载失败： url:{},file name:{}".format(url, file_name))


def demo():
    # url = "http://www.jiangxi.gov.cn/module/xxgk/search.jsp?texttype=0&fbtime=-1&vc_all=%E6%8A%BD%E6%A3%80&currpage=6&sortfield=compaltedate:0"
    # data = base_req(url, type='post', data={"page_num": 6})
    # data_html = load_html(data)
    # a = get_page_url(data_html)
    # print(a)
    # print(len(a))

    url = "http://www.jiangxi.gov.cn/art/2019/6/12/art_18819_699133.html"
    data = page_detail(url, "")
    print(data)

if __name__ == '__main__':
    demo()
