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


def retry_post(url):
    # url = "http://www.sdfda.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=60&perpage=20"
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    data = {"col": "1",
            "appid": "1",
            "webid": "35",
            "path": "/",
            "columnid": "8415",
            "sourceContentType": "1",
            "unitid": "41618",
            "webname": "山东省食品药品监督管理局",
            "permissiontype": "0"}
    s = requests.session()
    s.keep_alive = False
    re_data = s.post(url, data=data, headers=headers)
    return re_data


def base_req(url, type='get'):
    num = 5
    while num > 0:
        if type == 'get':
            data = retry_get(url)
        else:
            data = retry_post(url)
        if data.status_code < 400:
            return data
        else:
            num -= 1
    return ""


def load_html(req):
    req_data = req.content.decode()
    return lxml.etree.HTML(req_data)


def title_page(url, need_time):
    # need_time = "2000-06-18"
    page_data = base_req(url, type='post')
    if not page_data:
        return []
    data_list = []
    el_str = page_data.content.decode()
    for item in re.findall("\<table.*?\<\/table\>", el_str):
        try:
            item_tree = lxml.etree.HTML(item)
            link = item_tree.xpath('//tr/td[2]/a/@href')[0]
            link_time = item_tree.xpath('//tr/td[3]/span/text()')[0]
            if link_time > need_time:
                data_list.append({'page_url': 'http://www.sdfda.gov.cn{}'.format(link), 'page_time': link_time,
                                  'count_url': url})
        except:
            print("解析列表页面错误：{}".format(url))
            traceback.print_exc()
    return data_list


def page_detail(url, link_time, count_url):
    data_list = []
    try:
        need_type = ['xlsx', 'xls', 'csv']
        page_data = base_req(url)
        page_tree = load_html(page_data)
        a_link_list = page_tree.xpath('//a[starts-with(@href,"/module/download")]')
        page_title = page_tree.xpath('//tr/td[@class="title"]/text()')[0]
        if '食品' not in page_title:
            return []
        for link_item in a_link_list:
            try:
                link = link_item.xpath('@href')[0]
                file_name = link_item.xpath('string(.)')
                link_type = link.split('.')[-1]
                if (link_type not in need_type) or ('合格' not in file_name):
                    continue
                down_name = "{}{}@{}.{}".format(page_title, file_name, link_time, link_type)
                data_list.append({'url': 'http://www.sdfda.gov.cn{}'.format(link), 'name': down_name,
                                  'page_url': url, 'page_title': page_title, 'count_url': count_url})
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
    url = "http://www.sdfda.gov.cn/col/col8415/index.html?uid=41618&pageNum=1"
    url = "http://www.sdfda.gov.cn/art/2016/3/16/art_8415_638386.html"
    url = "http://www.sdfda.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=61&endrecord=120&perpage=20"
    file_url = "http://www.sdfda.gov.cn/module/download/downfile.jsp?classid=0&filename=b43afaa82e3d4466805ae00ef253c42a.xlsx"
    file_path = r"F:\PingAn_data\Food\shandong\demo.xlsx"
    data = title_page(url, '2000-00-00')
    for item in data:
        print(item)
    print(len(data))


if __name__ == '__main__':
    # demo()
    for i in range(1, 1000, 61):
        print(i, i + 60)