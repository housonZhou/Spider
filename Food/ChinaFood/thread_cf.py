import threading
import json
from queue import Queue
from Food.ChinaFood.cf_req import *


def start_4_pro(time_map, q):
    cl_first = Crawl()
    start_json = {'重庆': 'http://samr.cfda.gov.cn/WS01/CL1688/search.html?sort=true&sortId=CTIME&record=200&columnid=CLID|BCID&relation=MUST|MUST&tableName=Region&colNum=2&qryNum=2&curPage=1&qryidstr=CLID|BCID&qryValue=cl1688%7C0022',
                  '陕西': 'http://samr.cfda.gov.cn/WS01/CL1688/search.html?sort=true&sortId=CTIME&record=200&columnid=CLID|BCID&relation=MUST|MUST&tableName=Region&colNum=2&qryNum=2&curPage=1&qryidstr=CLID|BCID&qryValue=cl1688%7C0027'}
    for k, v in start_json.items():
        url = v
        print(url)
        try:
            cl_first.wait_for(url)
            time.sleep(5)
            html_tree = cl_first.page_tree()
            page_list = get_page_url(html_tree, time_map)
            for item in page_list:
                q.put((item, k))
        except:
            print('解析列表页面出错, url: {}'.format(url))
            traceback.print_exc()
    cl_first.driver().quit()


def start(start_list, need_list, save_dir, qp):
    for item in start_list:
        name = item.get('name')
        for pro_name in need_list:
            if pro_name in name:
                item['save_dir'] = os.path.join(save_dir, pro_name)
                qp.put(item)


def consumer(q):
    cl = Crawl()
    while True:
        if q.empty():
            time.sleep(1)
        data, city_name = q.get()
        page_url = data.get("page_url")
        page_time = data.get("page_time")
        cl.wait_for(page_url)
        page_tree = cl.page_tree()
        down_data = page_detail(page_url, page_tree, page_time)
        for item in down_data:
            item['city'] = city_name
            print(item)
            # json_f.write(json.dumps(item, ensure_ascii=False) + '\n')
            # json_f.flush()
            # down_file(url, save_dir, file_name)


def get_json(json_path):
    with open(json_path, 'r', encoding='utf8')as f:
        for line in f:
            yield json.loads(line.strip())


def consumer_download(qp):
    while not qp.empty():
        item = qp.get()
        url = item.get('url')
        file_name = item.get('name')
        base_path = item.get('save_dir')
        try:
            print('正在下载文件 ', url, file_name)
            down_file(url, file_name, base_path)
        except:
            print('文件下载失败： {}'.format(url))
            traceback.print_exc()


def run_pro():
    q_run = Queue()
    th_num = 4
    json_path = r'C:\Users\17337\houszhou\data\SpiderData\Food\china\0626_1425.json'
    base_path = r'C:\Users\17337\houszhou\data\SpiderData\Food\china\0626_1038\重庆'
    data_list = get_json(json_path)
    for item in data_list:
        name = item.get('name')
        city_name = item.get('city')
        if city_name == '重庆' and '重庆' not in name:
            print('put data', item)
            q_run.put(item)
    for _ in range(th_num):
        th = threading.Thread(target=consumer_download, args=(q_run, base_path))
        th.start()


def run_download_excel():
    th_num = 4
    need_list = ['广东', '广西']
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\Food\china\0626_1810'
    save_json = r'C:\Users\17337\houszhou\data\SpiderData\Food\china\0626_0941.json'
    start_list = get_json(save_json)
    q_link = Queue()
    start(start_list, need_list, save_dir, q_link)
    for _ in range(th_num):
        th = threading.Thread(target=consumer_download, args=(q_link, ))
        th.start()


if __name__ == '__main__':
    run_download_excel()
