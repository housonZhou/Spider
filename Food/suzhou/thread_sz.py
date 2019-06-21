import threading
import traceback
from queue import Queue
from Food.suzhou.sz_req import *


def start(time_map, q):
    base_url = 'http://www.suzhoufda.gov.cn/search.html?channel=&keyword=%E9%A3%9F%E5%93%81%E5%AE%89%E5%85%A8%E7%9B' \
               '%91%E7%9D%A3%E6%8A%BD%E6%A3%80%E4%BF%A1%E6%81%AF%E7%9A%84%E5%85%AC%E5%91%8A&page={}'
    for i in range(1, 10):
        url = base_url.format(i)
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
        try:
            page_url = data.get("page_url")
            page_time = data.get("page_time")
            down_data = page_detail(page_url, page_time)
            for item in down_data:
                url = item.get("url")
                file_name = item.get("name")
                print(item)
                down_file(url, save_dir, file_name)
        except:
            print("error: {}".format(data))
            traceback.print_exc()


if __name__ == '__main__':
    q_link = Queue()
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\suzhou\0620'
    time_end = ''
    th_num = 3
    th = threading.Thread(target=start, args=(time_end, q_link))
    th.start()
    time.sleep(10)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
