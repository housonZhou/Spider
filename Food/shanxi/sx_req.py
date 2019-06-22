import requests
import os
import re
import lxml
import time
import random
import traceback
from lxml import etree
from fake_useragent import UserAgent


def retry_get(url, post_data):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    s = requests.session()
    s.keep_alive = False
    time.sleep(random.random())
    if post_data:
        headers.update(post_data)
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
            data = retry_get(url, post_data)
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
    odd_list = html_tree.xpath('//*[starts-with(@id,"line_u25")]')
    data = []
    for item in odd_list:
        try:
            link = item.xpath('a/@href')[0]
            link = re.sub('\.\.\/\.\.', 'http://snamr.snaic.gov.cn', link)
            link_time = item.xpath('dfn/text()')[0]
            # link_time = re.findall('\d{4}\-\d{2}\-\d{2}', link_time)[0]
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
        a_link_list = page_tree.xpath('//a[starts-with(@href,"/system/_content/")]')
        page_title = page_tree.xpath('string(//div[@class="release"]/h2)')
        if '食品' not in page_title:
            return []
        for link_item in a_link_list:
            try:
                link = link_item.xpath('@href')[0]
                file_name = link_item.xpath('string(.)')
                link_type = file_name.split('.')[-1]
                if (link_type not in need_type) or ('合格' not in file_name):
                    continue
                if "不合格" in file_name:
                    tag = "_不合格信息_"
                else:
                    tag = "_合格信息_"
                down_name = "{}{}{}@{}.{}".format(page_title, file_name, tag, link_time, link_type)
                data_list.append({'url': 'http://snamr.snaic.gov.cn{}'.format(link), 'name': down_name,
                                  'page_url': url, 'page_title': page_title})
            except:
                print("解析下载文件错误：{}".format(url))
                traceback.print_exc()
    except:
        print("解析目标详情页面错误：{}".format(url))
        traceback.print_exc()
    return data_list


def down_file(url, save_dir, file_name, post_data):
    try:
        file_name = re.sub('[\\\/\:\*\?\"\<\>\→]', '_', file_name)
        with open(os.path.join(save_dir, "{}".format(file_name)), 'wb')as f:
            file_data = base_req(url, post_data=post_data)
            if file_data:
                f.write(file_data.content)
                print("文件下载成功")
            else:
                print("下载失败： url:{}\nfile name:{}".format(url, file_name))
    except:
        print("下载失败： url:{}\nfile name:{}".format(url, file_name))
        traceback.print_exc()


def demo():
    # url = "http://snamr.snaic.gov.cn/sjxw/sjzx1/zyfb.htm"
    # data = base_req(url, method_type='post', post_data={"page_num": "1"})
    # data_html = load_html(data)
    # a = get_page_url(data_html, '')
    # print(a)
    # print(len(a))

    # url = "http://snamr.snaic.gov.cn/info/1216/1678.htm"
    # data = page_detail(url, "")
    # print(data)

    url = 'http://snamr.snaic.gov.cn/system/_content/download.jsp?urltype=news.DownloadAttachUrl&owner=1502450578&wbfileid=10316372'
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\shanxi'
    file_name = 'demo2.xls'
    post_data = {'Cookie': 'JSESSIONID=F7B28AC1AF3EB939F817EF8F3E312EE9; coverlanguage_bb=0',
                 'Referer': 'http://snamr.snaic.gov.cn/info/1216/2108.htm'}
    down_file(url, save_dir, file_name, post_data)


if __name__ == '__main__':
    demo()
