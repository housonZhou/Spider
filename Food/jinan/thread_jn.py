import threading
from queue import Queue
from Food.jinan.jn_req import *


def start(time_map, q):
    url = 'http://fda.jinan.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=71&perpage=40'
    print(url)
    data = base_req(url, method_type='post')
    data_html = data.content.decode()
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
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\jinan\0628'
    time_end = ''
    th_num = 3
    th = threading.Thread(target=start, args=(time_end, q_link))
    th.start()
    time.sleep(10)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
