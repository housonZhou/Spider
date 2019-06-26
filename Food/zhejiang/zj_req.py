import requests
import os
import re
import lxml
import time
import random
import traceback
from lxml import etree
from fake_useragent import UserAgent


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
    odd_list = html_tree.xpath('//*[@id="NewsLists"]/table/tr')
    data = []
    for item in odd_list:
        try:
            link = item.xpath('td[1]/a/@href')[0]
            link_time = item.xpath('td[2]/text()')[0]
            link_time = re.findall('\d{4}\-\d{2}\-\d{2}', link_time)[0]
            if link_time > time_map:
                data.append({'page_url': "http://zjamr.zj.gov.cn{}".format(link), 'page_time': link_time})
        except:
            print("解析列表页面出错：")
            traceback.print_exc()
    return data


def page_detail(url, link_time):
    data_list = []
    try:
        need_type = ['xlsx', 'xls', 'csv']
        page_data = base_req(url)
        page_tree = load_html(page_data)
        a_link_list = page_tree.xpath('//a[starts-with(@href,"/uploadFiles/")]')
        page_title = page_tree.xpath('string(//div[@class="nr"]/h1)')
        # print(len(a_link_list))
        # print("page_title", page_title)
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
                data_list.append({'url': 'http://zjamr.zj.gov.cn{}'.format(link), 'name': down_name,
                                  'page_url': url, 'page_title': page_title})
            except:
                print("解析下载文件错误：{}".format(url))
                traceback.print_exc()
    except:
        print("解析目标详情页面错误：{}".format(url))
        traceback.print_exc()
    return data_list


def down_file(url, save_dir, file_name, data=None):
    try:
        with open(os.path.join(save_dir, "{}".format(file_name)), 'wb')as f:
            file_data = base_req(url, data=data)
            if file_data:
                f.write(file_data.content)
                print("文件下载成功")
            else:
                print("下载失败： url:{}\nfile name:{}".format(url, file_name))
    except:
        print("下载失败： url:{}\nfile name:{}".format(url, file_name))
        traceback.print_exc()


def demo():
    # url = "http://zjamr.zj.gov.cn/gggs/1.htm"
    # data = base_req(url)
    # data_html = load_html(data)
    # a = get_page_url(data_html, "")
    # print(a)
    # print(len(a))

    url = "http://zjamr.zj.gov.cn/HTML/gggs/201906/05e5d4cb-425e-49a4-8109-0ce64ce469c4.html"
    data = page_detail(url, "")
    print(data)

    # url = "http://www.jiangxi.gov.cn/uploadFiles/2019/06/食品抽检不合格-20190604090630.xls"
    # save_dir = r"F:\PingAn_data\Food\zhejiang\0619"
    # down_file(url, save_dir, "test.xls")


if __name__ == '__main__':
    demo()
