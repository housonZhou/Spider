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
        'text': '食品安全监督抽检信息公示',
        'currentPageNo': page_num,
        'pagination_input': ''
    }
    s = requests.session()
    s.keep_alive = False
    re_data = s.post(url, data=data, headers=headers)
    return re_data


def base_req(url, method_type='get', post_data={}):
    num = 5
    while num > 0:
        if method_type == 'get':
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
    odd_list = html_tree.xpath('//*[@id="list"]/li')
    data = []
    for item in odd_list:
        try:
            link = item.xpath('a/@onclick')
            link = 'http://scjg.nx.gov.cn/article/{}.html'.format(re.findall('\d+', link[0])[0])
            link_time = item.xpath('span/text()')[0]
            link_time = re.findall('\d{4}\-\d{2}\-\d{2}', link_time)[0]
            if link_time > time_map:
                data.append({'page_url': link, 'page_time': link_time})
        except:
            continue
    return data


def page_detail(url, link_time):
    data_list = []
    try:
        need_type = ['xlsx', 'xls', 'csv']
        page_data = base_req(url)
        page_tree = load_html(page_data)
        a_link_list = page_tree.xpath('//a[starts-with(@href,"/upload/file/")]')
        page_title = page_tree.xpath('string(//*[@id="at"])')
        if '食品' not in page_title:
            return []
        for link_item in a_link_list:
            try:
                link = link_item.xpath('@href')[0]
                file_name = link_item.xpath('string(.)')
                link_type = link.split('.')[-1]
                if (link_type not in need_type) or ('合格' not in file_name):
                    continue
                label = re.findall('(.*?)监督抽检', file_name)
                label = re.sub('[1-9\.\:\：附件]', '', label[0]) if label else "无分类"
                down_name = "{}{}-{}-@{}.{}".format(page_title, file_name, label, link_time, link_type)
                data_list.append({'url': 'http://scjg.nx.gov.cn{}'.format(link), 'name': down_name,
                                  'page_url': url, 'page_title': page_title})
            except:
                print("解析下载文件错误：{}".format(url))
                traceback.print_exc()
    except:
        print("解析目标详情页面错误：{}".format(url))
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
    # url = "http://scjg.nx.gov.cn/admin/article/query"
    # data = base_req(url, method_type='post', post_data={"page_num": "1"})
    # data_html = load_html(data)
    # a = get_page_url(data_html, '')
    # print(a)
    # print(len(a))

    url = "http://scjg.nx.gov.cn/article/571.html"
    data = page_detail(url, "")
    print(data)


if __name__ == '__main__':
    demo()
