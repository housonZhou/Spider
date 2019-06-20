import threading
from queue import Queue
from jx_req import *


def start(time_map, q):
    for i in range(1, 7):
        url = 'http://www.jiangxi.gov.cn/module/xxgk/search.jsp?texttype=0&fbtime=-1&vc_all=%E6%8A%BD%E6%A3%80&currpage={}&sortfield=compaltedate:0'.format(i)
        print(url)
        page_data = base_req(url, type='post', post_data={"page_num": i})
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
            print(down_data)
            down_file(url, save_dir, file_name)


if __name__ == '__main__':
    q_link = Queue()
    save_dir = r'F:\PingAn_data\Food\jiangxi\0619'
    time_end = ''
    th_num = 4
    th = threading.Thread(target=start, args=(time_end, q_link))
    th.start()
    time.sleep(10)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
