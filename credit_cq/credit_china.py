import json
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from tools.base_code import BaseCode

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def retry(count=5, default_return=None, sleep_time=0):
    def _first(func):
        def _next(*args, **kwargs):
            nonlocal count
            count -= 1
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                print('func: {}, error: {}'.format(func.__name__, e))
                time.sleep(sleep_time)
                result = _next(*args, **kwargs) if count > 0 else default_return
            return result
        return _next
    return _first


@retry(sleep_time=1)
def base_req(url, **kwargs):
    time.sleep(.2)
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': 'https://www.creditchina.gov.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Referer': 'https://www.creditchina.gov.cn/xinyongfuwu/shouxinhongmingdan/',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    if 'headers' in kwargs:
        kwargs['headers'].update(headers)
    resp = requests.get(url, verify=False, **kwargs)
    return resp


class CreditSpider:
    def __init__(self):
        self.need = {'守信激励': 4, '失信惩戒': 5, '行政处罚': 3, '行政许可': 2}
        # self.need = {'行政处罚': 3}
        self.city = '重庆两江新区'
        self.list_url = 'https://public.creditchina.gov.cn/private-api/typeNameAndCountSearch?keyword={city}' \
                        '&type={need}&searchState=2&entityType=1,2,3,7&page={page}&pageSize=100'
        self.need_url = 'https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type={need}&' \
                        'searchState=1&entityType={entity_type}&scenes=defaultscenario&keyword={company}' \
                        '&page={page}&pageSize=100'
        self.info_url = 'https://public.creditchina.gov.cn/private-api/getTyshxydmDetailsContent?keyword={key_word}' \
                        '&scenes=defaultscenario&entityType={entity_type}&searchState=1&uuid=&tyshxydm='
        self.page_url = 'https://www.creditchina.gov.cn/xinyongxinxixiangqing/xyDetail.html?tagNum={num}&' \
                        'searchState=1&entityType={entity_type}&keyword={name}'
        self.path = r'C:\Users\17337\houszhou\data\SpiderData\重庆两江信用\test\1719_{}.json'
        self.file_dict = {}
        self.open()

    def __del__(self):
        for need, file in self.file_dict.items():
            file.close()
            change(self.path.format(need))

    def open(self):
        for need in self.need:
            self.file_dict[need] = open(self.path.format(need), 'a', encoding='utf8')

    def main(self):
        # 四大类别
        for need in self.need:
            for company in self.company_list(need):
                info = self.company_info(company)
                self.company_detail(company, info)

    def company_list(self, need, index=1):
        """获取所有公司/机构名称和类型"""
        url = self.list_url.format(city=self.city, need=need, page=index)
        resp = base_req(url)
        if resp:
            result = json.loads(resp.content.decode())
            if result.get('message') != '成功':
                print('data error: \nurl: {}, result: {}'.format(url, result))
                return
            result = result.get('data')
            page = result.get('page', index)
            total_size = result.get('totalSize', 0)
            list_data = result.get('list')
            for item in list_data:
                name = item.get('name')
                entity_type = item.get('entity_type')
                yield {'name': name, 'need': need, 'entity_type': entity_type}
            if total_size > page:
                yield from self.company_list(need, index=page + 1)

    def company_detail(self, company, info, index=1):
        """获取公司该类型下奖励/处罚/登记信息"""
        name = company.get('name')
        need = company.get('need')
        entity_type = company.get('entity_type')
        url = self.need_url.format(need=need, company=name, page=index, entity_type=entity_type)
        resp = base_req(url)
        if resp:
            result = json.loads(resp.content.decode())
            if result.get('message') != '成功':
                print('data error: \nurl: {}, result: {}'.format(url, result))
                return
            result = result.get('data')
            page = result.get('page', index)
            total_size = result.get('totalSize', 0)
            list_data = result.get('list')
            total = result.get('total')
            self.page_detail(list_data, need, info, total, company)
            if total_size > page:
                self.company_detail(company, info, index=page + 1)

    def company_info(self, company: dict):
        """获取公司的基本信息"""
        name = company.get('name')
        entity_type = company.get('entity_type')
        url = self.info_url.format(key_word=name, entity_type=entity_type)
        resp = base_req(url)
        if resp:
            result = json.loads(resp.content.decode())
            if result.get('message') != '成功':
                print('data error: \nurl: {}, result: {}'.format(url, result))
                return
            result = result.get('data')
            data = result.get('data')
            head_entity = result.get('headEntity')
            new = self._info(data) if data else {}
            new.update({'企业名称': head_entity.get('jgmc', name), '企业状态': head_entity.get('status'),
                        '统一社会信用代码': head_entity.get('tyshxydm'),
                        '失信惩戒对象': result.get('punishmentStatus', 'no'),
                        '守信激励对象': result.get('rewardStatus', 'no')})
            return new

    def page_detail(self, list_data, need, info, total, company):
        for item in list_data:
            url = self.page_url.format(num=self.need[need], name=company.get('name'),
                                       entity_type=company.get('entity_type'))
            new = self._info(item)
            new.update(info)
            new.update({'记录次数': total, 'need': need,
                        '链接': url})
            print(new)
            self.write(new)

    def write(self, data):
        file = self.file_dict.get(data.get('need'))
        file.write(json.dumps(data, ensure_ascii=False) + '\n')
        file.flush()

    @staticmethod
    def _info(item):
        column_list = item.get('columnList')
        entity = item.get('entity')
        sences_map = item.get('sencesMap')
        data_source = item.get('dataSource')
        data_catalog = item.get('data_catalog')
        new = {sences_map.get(i): entity.get(i) for i in column_list}
        new.update({'data_source': data_source, 'data_catalog': data_catalog})
        return new


def loop(n):
    for i in range(5):
        yield i
    if n > 1:
        print('n', n)
        yield from loop(n - 1)


def test():
    cs = CreditSpider()
    cs.main()


def change(json_path: str):
    # json_path = r'C:\Users\17337\houszhou\data\SpiderData\重庆两江信用\test_行政处罚.json'
    excel_path = json_path.replace('.json', '.xlsx')
    bc.json2excel(bc.get_data_from_json(json_path), excel_path, index=False)


if __name__ == '__main__':
    bc = BaseCode()
    test()
