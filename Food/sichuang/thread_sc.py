import threading
from queue import Queue
from sc_req import *


def start(time_map, q):
    url_list = ['http://scjgj.sc.gov.cn/ztlm/ccxx/index.html',
                'http://scjgj.sc.gov.cn/ztlm/ccxx/index_1.html',
                'http://scjgj.sc.gov.cn/ztlm/ccxx/index_2.html',
                'http://scjgj.sc.gov.cn/ztlm/ccxx/index_3.html']
    for url in url_list:
        print(url)
        page_data = base_req(url)
        html_tree = load_html(page_data)
        page_list = get_page_url(html_tree, time_map)
        for item in page_list:
            q.put(item)


def consumer(q):
    while True:
        if q.empty():
            time.sleep(1)
        data = q.get()
        page_url = data.get("page_url")
        page_time = data.get("page_time")
        down_data = page_detail(page_url, page_time)
        for item in down_data:
            url = item.get("url")
            file_name = item.get("name")
            print(item)
            down_file(url, save_dir, file_name)


if __name__ == '__main__':
    q_link = Queue()
    save_dir = r'F:\PingAn_data\Food\sichuang\0619'
    time_end = ''
    th_num = 4
    th = threading.Thread(target=start, args=(time_end, q_link))
    th.start()
    time.sleep(10)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
