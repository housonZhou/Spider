import threading
from queue import Queue
from Food.huaian.ha_req import *


def start(time_map, q):
    base_url = 'http://scjgj.huaian.gov.cn/col/7958_211358/index{}.html'
    for i in range(1, 35):
        count = '' if i == 1 else '_{}'.format(i)
        url = base_url.format(count)
        print(url)
        data = base_req(url)
        if not data:
            continue
        data_html = load_html(data)
        page_list = get_page_url(data_html, time_map)
        for item in page_list:
            q.put(item)


def consumer(q):
    while not q.empty():
        data = q.get()
        try:
            page_url = data.get("page_url")
            page_time = data.get("page_time")
            down_data = page_detail(page_url, page_time)
            for item in down_data:
                url = item.get("url")
                file_name = item.get("name")
                down_file(url, save_dir, file_name)
        except:
            print('error: {}'.format(data))
            traceback.print_exc()


if __name__ == '__main__':
    q_link = Queue()
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\huaian\0702'
    time_end = ''
    th_num = 3
    th = threading.Thread(target=start, args=(time_end, q_link))
    th.start()
    time.sleep(10)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
