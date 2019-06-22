import threading
from queue import Queue
from Food.shanxi.sx_req import *


def start(time_map, q):
    # http://snamr.snaic.gov.cn/sjxw/sjzx1/zyfb/1.htm
    # http://snamr.snaic.gov.cn/sjxw/sjzx1/zyfb/5.htm
    # http://snamr.snaic.gov.cn/sjxw/sjzx1/zyfb.htm
    for i in range(6):
        base_url = 'http://snamr.snaic.gov.cn/sjxw/sjzx1/zyfb{}.htm'
        count = '' if i == 0 else '/{}'.format(i)
        url = base_url.format(count)
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
            continue
        data = q.get()
        try:
            page_url = data.get("page_url")
            page_time = data.get("page_time")
            down_data = page_detail(page_url, page_time)
            for item in down_data:
                url = item.get("url")
                file_name = item.get("name")
                print(down_data)
                post_data = {'Cookie': 'JSESSIONID=F7B28AC1AF3EB939F817EF8F3E312EE9; coverlanguage_bb=0',
                             'Referer': page_url}
                down_file(url, save_dir, file_name, post_data)
        except:
            print('error: {}'.format(data))
            traceback.print_exc()


if __name__ == '__main__':
    q_link = Queue()
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\shanxi\0622'
    time_end = ''
    th_num = 3
    th = threading.Thread(target=start, args=(time_end, q_link))
    th.start()
    time.sleep(10)
    for _ in range(th_num):
        th = threading.Thread(target=consumer, args=(q_link, ))
        th.start()
