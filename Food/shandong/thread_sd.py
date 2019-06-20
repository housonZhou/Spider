import threading
from queue import Queue
from shandong import *


def start(time_map, q):
    for i in range(1, 1000, 61):
        url = 'http://www.sdfda.gov.cn/module/web/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=20'.format(i, i + 60)
        print(url)
        page_list = title_page(url, time_map)
        for item in page_list:
            q.put(item)


def consumer(q):
    global count
    while True:
        if q.empty():
            time.sleep(1)
        data = q.get()
        page_url = data.get("page_url")
        page_time = data.get("page_time")
        count_url = data.get("count_url")
        down_data = page_detail(page_url, page_time, count_url)
        for item in down_data:
            url = item.get("url")
            file_name = item.get("name")
            print(down_data)
            count += 1
            down_file(url, save_dir, file_name)


if __name__ == '__main__':
    count = 0
    q_link = Queue()
    save_dir = r'F:\PingAn_data\Food\shandong\0618'
    time_end = '2000-06-06'
    th_num = 4
    th = threading.Thread(target=start, args=(time_end, q_link))
    th.start()
    time.sleep(10)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
