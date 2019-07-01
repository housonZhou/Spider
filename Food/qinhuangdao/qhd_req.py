import requests
import os
import re
import lxml
import json
import time
import random
import traceback
from lxml import etree
from fake_useragent import UserAgent


def retry_get(url, post_data):
    ua = UserAgent()
    headers = {"User-Agent": ua.random,
               "Cookie": "JSESSIONID=191BEB6C933CC088E11E01F3437AEDBB",
               "Origin": "http://fda.jinan.gov.cn",
               "Referer": "http://fda.jinan.gov.cn/col/col8191/index.html?uid=8093&pageNum=3",
               "X-Requested-With": "XMLHttpRequest"}
    s = requests.session()
    s.keep_alive = False
    time.sleep(random.random())
    if post_data:
        headers.update(post_data)
    req = s.get(url, headers=headers, verify=False)
    return req


def retry_post(url, post_data):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    s = requests.session()
    s.keep_alive = False
    re_data = s.post(url, data=post_data, headers=headers)
    return re_data


def base_req(url, method_type='get', post_data=None):
    num = 5
    while num > 0:
        if method_type == 'get':
            data = retry_get(url, post_data)
        else:
            data = retry_post(url, post_data)
        if data.status_code < 400:
            return data
        else:
            num -= 1
    print('url: {} 下载重试失败'.format(url))
    return ""


def load_html(req):
    try:
        req_data = req.content.decode()
    except UnicodeDecodeError:
        req_data = req.content.decode('gbk')
    return lxml.etree.HTML(req_data)


def get_page_url(html_tree, time_map):
    odd_list = json.loads(html_tree).get('rows')
    data = []
    print(odd_list)
    for item in odd_list:
        try:
            fid = item.get('fid')
            fdate = item.get('fdate')
            link = 'http://www.qhdfma.gov.cn/business/TBColumnsAction_getNoticeData.do?ftype={}'.format(fid)
            link_time = fdate.replace('/', '-')
            if link_time > time_map:
                data.append({'page_url': link, 'page_time': link_time})
        except:
            print('error: 解析json数据出错 {}'.format(data))
            traceback.print_exc()
            continue
    return data


def page_detail(url, link_time):
    page_data = base_req(url, method_type='post')
    json_data = json.loads(page_data.content.decode())
    page_tree = lxml.etree.HTML(json_data.get('rows')[0].get('fcontent'))
    data_list = []
    page_title = json_data.get('rows')[0].get('ftitle')
    need_type = ['xlsx', 'xls', 'csv']
    a_link_list = page_tree.xpath('//a[starts-with(@href, "/ueditor/jsp/upload/file")]')
    if '食品' not in page_title:
        return []
    for link_item in a_link_list:
        try:
            link = link_item.xpath('@href')[0]
            file_name = link_item.xpath('string(.)').strip()
            link_type = link.split('.')[-1]
            if (link_type not in need_type) or ('合格' not in file_name):
                continue
            tag = "_不合格信息_" if "不合格" in file_name else "_合格信息_"
            down_name = "{}{}{}@{}.{}".format(page_title, file_name, tag, link_time, link_type)
            data_list.append({'url': 'http://www.qhdfma.gov.cn{}'.format(link), 'name': down_name,
                              'page_url': url, 'page_title': page_title})
        except:
            print("解析下载文件错误：{}".format(url))
            traceback.print_exc()
    return data_list


def down_file(url, save_dir, file_name):
    try:
        file_name = re.sub('[\\\/\:\*\?\"\<\>\→]', '_', file_name)
        with open(os.path.join(save_dir, "{}".format(file_name)), 'wb')as f:
            file_data = base_req(url)
            if file_data:
                f.write(file_data.content)
                print("文件下载成功")
            else:
                print("下载失败： url:{}\nfile name:{}".format(url, file_name))
    except:
        print("下载失败： url:{}\nfile name:{}".format(url, file_name))
        traceback.print_exc()


def demo():
    # url = 'http://www.qhdfma.gov.cn/business/TBColumnsAction_getload.do'
    # data = {'ftype': '57', 'page': '1'}
    # data = base_req(url, method_type='post', post_data=data)
    # data_html = data.content.decode()
    # print(data_html)
    # a = get_page_url(data_html, '')
    # print(a)
    # print(len(a))

    url = 'http://www.qhdfma.gov.cn/business/TBColumnsAction_getNoticeData.do?ftype=6999'
    data = page_detail(url, '')
    print(data)

    # url = 'http://yjj.hebei.gov.cn/directory/web/WS01/images/yrPGt7PpvOy6z7jxLTIwMTkwNTIwLnhscw==.xls'
    # save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\shanxi'
    # file_name = 'demo_new.xls'
    # down_file(url, save_dir, file_name)


if __name__ == '__main__':
    demo()
