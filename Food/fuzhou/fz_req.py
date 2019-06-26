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


def find_data(key_str, item):
    use = re.findall('"{}":"(.*?)"'.format(key_str), item)
    return use[0] if use else ''


def get_page_url(page_data, time_map):
    page_data = page_data.content.decode()
    data_list = re.findall('(\{[\s\S]*?\"title\"[\s\S]*?\})', page_data)
    for item in data_list:
        try:
            link = find_data('url', item)
            link_time = find_data('time', item)
            title = find_data('title2', item)
            file = find_data('file', item)
            filedesc = find_data('filedesc', item)
            if file and ('食品' in title) and link_time > time_map:
                file_link_list = file.split(';')
                file_name_list = filedesc.split(';')
                for i in range(len(file_link_list)):
                    file_link = file_link_list[i]
                    file_name = file_name_list[i]
                    if '合格' not in file_name:
                        continue
                    link_type = file_link.split('.')[-1]
                    tag = "_不合格信息_" if "不合格" in file_name else "_合格信息_"
                    down_name = "{}{}{}@{}.{}".format(title, file_name, tag, link_time, link_type)
                    data = {'url': '{}/{}'.format('/'.join(link.split('/')[:-1]), file_link),
                            'name': down_name, 'page_url': link, 'page_title': title}
                    yield data
        except:
            print("解析列表页面出错：")
            traceback.print_exc()


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


if __name__ == '__main__':
    pass
