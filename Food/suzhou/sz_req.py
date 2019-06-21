import requests
import os
import re
import lxml
import time
import random
import traceback
from lxml import etree
from fake_useragent import UserAgent


def get_proxies():
    """获取代理,sogou的是http,微信界面的是https"""
    proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
        "host": '222.185.28.38',
        "port": '6442',
        "user": '16HEOFQR',
        "pass": '404729',
    }
    proxies = {
        "http": proxyMeta,
        "https": proxyMeta,
    }
    return proxies


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


def base_req(url, method_type='get', data=None):
    num = 5
    while num > 0:
        if method_type == 'get':
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
    odd_list = html_tree.xpath('//ul[@class="locationnew_ul"]/li')
    data = []
    for item in odd_list:
        try:
            link = item.xpath('div[1]/a/@href')[0]
            link_time = item.xpath('string(div[2])').strip()
            # link_time = re.findall('\d{4}\-\d{2}\-\d{2}', link_time)[0]
            if link_time > time_map:
                data.append({'page_url': "http://www.suzhoufda.gov.cn{}".format(link), 'page_time': link_time})
        except:
            print("解析列表页面出错：")
            traceback.print_exc()
    return data


def page_detail(url, link_time):
    data_list = []
    try:
        msg = {0: '合格产品信息', 1: '不合格产品信息'}
        need_type = ['xlsx', 'xls', 'csv']
        page_data = base_req(url)
        page_tree = load_html(page_data)
        page_title = page_tree.xpath('string(//div[@class="biaoti"]/div[1])').strip()
        a_link_list = page_tree.xpath('//a[starts-with(@href, "/upload/")]/@href')
        a_link_list = [i for i in a_link_list if i.split('.')[-1] in need_type]
        if '食品' not in page_title:
            return []
        count = 0
        if len(a_link_list) > 2:
            print('页面链接数据大于2：{}'.format(url))
            return []
        for link in a_link_list:
            link = 'http://www.suzhoufda.gov.cn{}'.format(link)
            file_name = msg[count]
            link_type = link.split('.')[-1]
            print('link: {} , file_name: {}'.format(link, file_name))
            tag = "_不合格信息_" if "不合格" in file_name else "_合格信息_"
            down_name = "{}{}{}@{}.{}".format(page_title, file_name, tag, link_time, link_type)
            data_list.append({'url': link, 'name': down_name, 'page_url': url, 'page_title': page_title})
            count += 1
    except:
        print("解析目标详情页面错误：{}".format(url))
        traceback.print_exc()
    return data_list


def down_file(url, save_dir, file_name, data=None):
    try:
        file_name = re.sub('[\\\/\:\*\?\"\<\>\→]', '_', file_name)
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
    # url = "http://www.suzhoufda.gov.cn/search.html?channel=&keyword=%E9%A3%9F%E5%93%81%E5%AE%89%E5%85%A8%E7%9B%91%E7%9D%A3%E6%8A%BD%E6%A3%80%E4%BF%A1%E6%81%AF%E7%9A%84%E5%85%AC%E5%91%8A&page=2"
    # data = base_req(url)
    # data_html = load_html(data)
    # a = get_page_url(data_html, "")
    # print(a)
    # print(len(a))

    url = "http://www.suzhoufda.gov.cn/gonggaogongshi_article-64-38410.html"
    data = page_detail(url, "")
    print(data)

    # url = "http://www.jiangxi.gov.cn/uploadFiles/2019/06/食品抽检不合格-20190604090630.xls"
    # save_dir = r"F:\PingAn_data\Food\zhejiang\0619"
    # down_file(url, save_dir, "test.xls")


if __name__ == '__main__':
    demo()
