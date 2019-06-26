import threading
import json
import traceback
from queue import Queue
from Food.fuzhou.fz_req import *


def start(time_map, q):
    url = 'http://scjg.fuzhou.gov.cn/was5/web/search?channelid=290792&templet=advsch.jsp&sortfield=-docreltime&classsql=doctitle%2Cdoccontent%2B%3D%25%E7%9B%91%E7%9D%A3%E6%8A%BD%E6%A3%80%E4%BF%A1%E6%81%AF%25*docpuburl%3D%27%25%2Fzz%2F%25%27*siteid%3D13&page=1&prepage=40'
    page_data = base_req(url)
    for item in get_page_url(page_data, time_map):
        print(item)
        q.put(item)


def consumer(q):
    while not q.empty():
        item = q.get()
        try:
            url = item.get("url")
            file_name = item.get("name")
            print(item)
            down_file(url, save_dir, file_name)
        except:
            print("error: {}".format(item))
            traceback.print_exc()


if __name__ == '__main__':
    q_link = Queue()
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\fuzhou\0626'
    time_end = ''
    th_num = 3
    start(time_end, q_link)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
