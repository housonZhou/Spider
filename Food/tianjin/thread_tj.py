import threading
import traceback
from queue import Queue
from Food.tianjin.tj_req import *


def start(time_map, q):
    base_url = 'http://scjg.tj.gov.cn/xwzx/gs/spcjxx/index{}.html'
    for i in range(3, 29):
        if i == 0:
            url_data = ""
        else:
            url_data = "_" + str(i)
        url = base_url.format(url_data)
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
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\tianjin\0620_1511'
    time_end = ''
    th_num = 2
    th = threading.Thread(target=start, args=(time_end, q_link))
    th.start()
    time.sleep(10)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
