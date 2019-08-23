import os
import requests
import json
import time
import pandas as pd
import numpy as np
from urllib import parse
from lxml.etree import HTML
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def base_req(url, need_byte=False, method='GET', **kwargs):
    base_headers = {
        'Cookie': 'insert_cookie=52179150; JSessionIDidh=lJTWdfCS0mtWnvTH5pvpzJr7VLvc3gvvTp3BWznSxc0nwNfHFgZ9!1968099050',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    kwargs.get('headers', {}).update(base_headers)
    s = requests.session()
    req_data = s.request(method, url, verify=False, **kwargs)
    if need_byte:
        return req_data.content
    try:
        return req_data.content.decode()
    except:
        return req_data.content.decode('gbk')


def get_one(url_id):
    url = 'http://pnr.sz.gov.cn/d-cyyf/houseBaseDelegate/getHouseInfoById.run?houseId={}'.format(url_id)
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://pnr.sz.gov.cn/d-cyyf/web/homeDetails.jsp?id={}'.format(url_id)
    }
    data = base_req(url, headers=headers)
    return json.loads(data)


def page_detail(house_id):
    json_data = get_one(house_id)
    purpose = {'0': '待定', '1': '办公', '2': '研发', '3': '厂房', '4': '仓库', '5': '商铺', '6': '其他用途'}
    main_purpose = json_data.get('main_purpose')
    data = {'项目名称': 'name', '信息更新日期': 'modify_date', '创新型产业用房建筑面积（平方米）': 'innovation_area',
            '未租售用房面积（平方米）': 'available_area', '租售性质': 'salerent_nature', '产权性质': 'property_type',
            '项目建设进度': 'building_proce', '所在辖区': 'canton_name', '具体位置': 'address', '图片': 'attach_xct1',
            '定位图': 'attach_wzt', '产权主体': 'porperty_name', '宗地用地面积（平方米）': 'land_area',
            '物业管理费（元/平方米·月）': 'management_fee', '项目总体情况描述': 'summary',
            '项目目前建设或租售工作开展的具体进度描述': 'salerent_procdetail', '项目租售进度': 'salerent_proce_name',
            '配套停车位（个）': 'packing_num', '创新型产业用房计划租售时间': 'salerent_time',
            '项目拟租售对象（或准入条件）': 'salerent_obj'}
    re_data = {
        '项目计划开工时间': '{}-{}'.format(json_data.get('plan_begin_year', ''), json_data.get('plan_begin_month', '')),
        '项目计划竣工时间': '{}-{}'.format(json_data.get('plan_end_year', ''), json_data.get('plan_end_month', '')),
        '原始网页链接': 'http://pnr.sz.gov.cn/d-cyyf/web/homeDetails.jsp?id={}#ad-image-0'.format(house_id),
        '主要用途': '-'.join(purpose.get(i, '') for i in main_purpose.split('-'))
    }
    for k, v in data.items():
        re_data[k] = json_data.get(v)
    return re_data


def get_img(uid, save_dir):
    if not uid:
        return
    url = 'http://pnr.sz.gov.cn/d-cyyf/downLoadServlet?attachType=house&table=bsb_hsrprj_base&thumbImg=true&' \
          'id={}'.format(uid)
    headers = {'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
               'Referer': 'http://pnr.sz.gov.cn/d-cyyf/cyyfmap/index.html'}
    with open(os.path.join(save_dir, '{}.jpg'.format(uid)), 'wb')as f:
        data = base_req(url, need_byte=True, headers=headers)
        f.write(data)


def _hd(url, save_dir, uid):
    if not url:
        return
    with open(os.path.join(save_dir, '{}.jpg'.format(uid)), 'wb')as f:
        headers = {'Referer': 'http://pnr.sz.gov.cn/d-cyyf/web/homeDetails.jsp?id=01130000000000000000000000000127'}
        data = base_req(url, need_byte=True, headers=headers)
        f.write(data)


def hd_img(data, save_dir):
    id_1, id_2 = data
    link_1, link_2 = post_img(id_1, id_2)
    _hd(link_1, save_dir, id_1)
    _hd(link_2, save_dir, id_2)


def post_img(id_1, id_2):
    url = 'http://pnr.sz.gov.cn/d-cyyf/houseBaseDelegate/getHousePicture.run'
    headers = {
        'Accept-Encoding': 'gzip, deflate',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://pnr.sz.gov.cn/d-cyyf/web/homeDetails.jsp?id=17ebc31f9fba409eaeabf8a9a1877eed',
        'Origin': 'http://pnr.sz.gov.cn',
        'Content-Length': '138',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    post_data = '["{}","","","","","{}",""]'.format(id_1, id_2)
    post_str = parse.quote(post_data)
    data = base_req(url, method='POST', headers=headers, data='xctArrs={}'.format(post_str))
    try:
        data = json.loads(data)
        print(data)
        return data[0].get('file_path'), data[-1].get('file_path')
    except Exception as e:
        print(e)
        return '', ''


def write(json_data, save_name):
    pf = pd.DataFrame(json_data)
    pf.to_excel(save_name, index=False)


def main():
    save_img = r'C:\Users\17337\houszhou\data\SpiderData\深圳产业空间地图\img'
    write_path = r'C:\Users\17337\houszhou\data\SpiderData\深圳产业空间地图\深圳产业空间地图数据.xlsx'
    url = 'http://pnr.sz.gov.cn/d-mapcyyf/mapservice/queryHouses'
    headers = {'Referer': 'http://pnr.sz.gov.cn/d-cyyf/cyyfmap/index.html'}
    data = base_req(url, headers=headers)
    data = json.loads(data)
    write_json = []
    for item in data:
        try:
            uid = item.get('HSRPRJ_ID') if item.get('HSRPRJ_ID') else item.get('PROJ_ID')
            page_data = page_detail(uid)
            write_json.append(page_data)
            print(page_data)
            get_img(page_data.get('图片'), save_img)
            get_img(page_data.get('定位图'), save_img)
        except Exception as e:
            print(e)
        time.sleep(3)
    write(write_json, write_path)


def save_hd():
    write_path = r'C:\Users\17337\houszhou\data\SpiderData\深圳产业空间地图\深圳产业空间地图数据.xlsx'
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\深圳产业空间地图\img_hd'
    pf = pd.read_excel(write_path, usecols=[8, 10], names=None)
    li = pf.values.tolist()
    for item in li:
        if np.nan in item:
            continue
        try:
            hd_img(item, save_dir)
        except Exception as e:
            print(item)
            print(e)


class SpiderDriver:
    def __init__(self, save_dir):
        self.opt = webdriver.ChromeOptions()
        # self.opt.add_argument('--headless')
        self.browser = webdriver.Chrome(options=self.opt)
        self.wait = WebDriverWait(self.browser, 20)
        self.save_dir = save_dir

    def __del__(self):
        self.browser.close()

    def get_img_url(self, url):
        re_list = []
        try:
            self.browser.get(url)
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="idSlider"]/li[1]/a/img')))
            time.sleep(2)
            page = self.browser.page_source
            tree = HTML(page)
            img_list = tree.xpath('//*[@id="idSlider"]/li/a/img/@src')
            print('img_list: ', img_list)
            for img in img_list:
                uid = img.split('/')[-1].split('.')[0]
                _hd(img, self.save_dir, uid)
                re_list.append(uid)
        except Exception as e:
            print(e)
        return json.dumps(re_list, ensure_ascii=False)


def main_all_img():
    write_path = r'C:\Users\17337\houszhou\data\SpiderData\深圳产业空间地图\深圳产业空间地图数据.xlsx'
    new_excel = r'C:\Users\17337\houszhou\data\SpiderData\深圳产业空间地图\深圳产业空间地图数据更新.xlsx'
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\深圳产业空间地图\img_all'
    pf = pd.read_excel(write_path)
    sd = SpiderDriver(save_dir)
    pf['图片列表'] = pf.get('原始网页链接').apply(sd.get_img_url)
    pf.to_excel(new_excel)


if __name__ == '__main__':
    main_all_img()
