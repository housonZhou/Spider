# -*- coding: utf-8 -*-
import json
import random
import time

import scrapy
from StatsGov.items import StatsgovItem
from StatsGov.settings import POST_HEADERS
from selenium import webdriver
from selenium.webdriver import ChromeOptions

from tools.base_code import parse2query

option = ChromeOptions()
option.add_experimental_option('excludeSwitches', ['enable-automation'])


class StatsGovSpider(scrapy.Spider):
    name = 'stats_gov'
    url_tree = 'http://data.stats.gov.cn/easyquery.htm'
    url_query = 'http://data.stats.gov.cn/easyquery.htm?'
    city = {"110000": "北京", "310000": "上海", "330100": "杭州", "420100": "武汉", "440100": "广州",
            "440300": "深圳", "500000": "重庆", "510100": "成都", "610100": "西安"}
    code_json = {
        # '年度': 'hgnd',
        # '季度': 'hgjd',
        # '月度': 'hgyd',
        # '主要城市月度': 'csyd',
        '主要城市年度': 'csnd'
    }

    # allowed_domains = ['http://data.stats.gov.cn/easyquery.htm?cn=B01']
    # start_urls = ['http://http://data.stats.gov.cn/easyquery.htm?cn=B01/']

    def start_requests(self):
        city_json = {'主要城市月度': 'csyd', '主要城市年度': 'csnd'}

        # yield from self.query_test()  # 测试
        # 先访问设置时间
        yield from self.reset_time()
        # 一般指标
        for k, v in self.code_json.items():
            # 实际接口入口
            data = {'id': 'zb', 'dbcode': v, 'wdcode': 'zb', 'm': 'getTree'}
            meta = {'parent': k + '指标', 'zb': k}
            yield scrapy.FormRequest(self.url_tree, formdata=data, headers=POST_HEADERS, callback=self.parse,
                                     meta=meta, dont_filter=True)
        """
        # 主要城市的地区数据
        for city_code, city_name in self.city.items():
            # 城市颗粒度
            for db_name, db_code in city_json.items():
                data = {'m': 'QueryData', 'dbcode': db_code, 'rowcode': 'zb', 'colcode': 'sj',
                        'wds': '[{"wdcode":"reg","valuecode":"%s"}]' % city_code, 'dfwds': '[]',
                        'k1': '1584671648941', 'h': '1'}
                url = parse2query(data, url_join=self.url_query)
                meta = {'parent': '{}-地区'.format(db_name + '指标'), 'zb': db_name}
                yield scrapy.Request(url, headers=POST_HEADERS, callback=self.detail, meta=meta, dont_filter=True)
        """

    def reset_time(self):
        for k, v in self.code_json.items():
            wds = '[{"wdcode":"reg","valuecode":"110000"}]' if '主要城市' in k else '[]'
            req_data = {'m': 'QueryData', 'dbcode': v, 'rowcode': 'zb', 'colcode': 'sj', 'wds': wds,
                        'dfwds': '[{"wdcode":"sj","valuecode":"2010-"}]'}
            url = parse2query(req_data, url_join=self.url_query)
            print('设置访问时间')
            yield scrapy.Request(url, headers=POST_HEADERS, callback=self.func_pass, priority=1, dont_filter=True)

    def query_test(self):
        v = 'hgnd'
        req_data = {'m': 'QueryData', 'dbcode': v, 'rowcode': 'zb', 'colcode': 'sj', 'wds': '[]',
                    'dfwds': '[{"wdcode":"sj","valuecode":"2010-"}]'}
        url = parse2query(req_data, url_join=self.url_query)
        yield scrapy.Request(url, headers=POST_HEADERS, callback=self.func_pass, priority=1, dont_filter=True)

        id_ = 'A0101'
        data = {'m': 'QueryData', 'dbcode': v, 'rowcode': 'zb', 'colcode': 'sj', 'wds': '[]',
                'dfwds': '[{"wdcode":"zb","valuecode":"%s"}]' % id_,
                'k1': '1584671648941', 'h': '1'}
        url = parse2query(data, url_join=self.url_query)
        yield scrapy.Request(url, headers=POST_HEADERS, callback=self.detail, dont_filter=True)

    def parse(self, response: scrapy.http.Response):
        zb = response.meta.get('zb')
        data_json = json.loads(response.body.decode())
        for item in data_json:
            id_ = item.get('id')
            isParent = item.get('isParent')
            name = item.get('name')
            wdcode = item.get('wdcode')
            dbcode = item.get('dbcode')
            meta = {'parent': '{}-{}'.format(response.meta.get('parent'), name), 'zb': zb}
            if isParent:
                data = {'id': id_, 'dbcode': dbcode, 'wdcode': wdcode, 'm': 'getTree'}
                yield scrapy.FormRequest(self.url_tree, formdata=data, headers=POST_HEADERS,
                                         callback=self.parse, meta=meta, dont_filter=True)
            elif '主要城市' in zb:
                for city_code, city_name in self.city.items():
                    data = {'m': 'QueryData', 'dbcode': dbcode, 'rowcode': 'zb', 'colcode': 'sj',
                            'wds': '[{"wdcode":"reg","valuecode":"%s"}]' % city_code,
                            'dfwds': '[{"wdcode":"zb","valuecode":"%s"}]' % id_,
                            'k1': '1584671648941', 'h': '1'}
                    url = parse2query(data, url_join=self.url_query)
                    time.sleep(random.random() + 0.5)
                    yield scrapy.Request(url, headers=POST_HEADERS, callback=self.detail, meta=meta, dont_filter=True)
            else:
                data = {'m': 'QueryData', 'dbcode': dbcode, 'rowcode': 'zb', 'colcode': 'sj', 'wds': '[]',
                        'dfwds': '[{"wdcode":"zb","valuecode":"%s"}]' % id_,
                        'k1': '1584671648941', 'h': '1'}
                url = parse2query(data, url_join=self.url_query)
                time.sleep(random.random() + 0.5)
                yield scrapy.Request(url, headers=POST_HEADERS, callback=self.detail, meta=meta, dont_filter=True)

    def detail(self, response: scrapy.http.Response):
        time.sleep(random.random() + 0.5)
        name_dict = {'zb': '指标', 'sj': '时间', 'reg': '地区'}
        content = response.body.decode()
        # print(content)
        data_json = json.loads(content)
        data = data_json.get('returndata')
        data_nodes = data.get('datanodes')
        wd_nodes = data.get('wdnodes')
        wd_dict = {}  # {'zb': {'A0101': {}, 'A0202': {}}, 'sj': {'2019D': {}, '2019C': {}}}
        for i in wd_nodes:
            wd_dict[i.get('wdcode')] = {j.get('code'): j for j in i.get('nodes')}
        # print('wd_dict', wd_dict)
        for item in data_nodes:
            wds = item.get('wds')
            item_data = item.get('data')
            has_data = '是' if item_data.get('hasdata') else '否'
            # print(has_data, item_data)
            item_dict = {'数据值': item_data.get('data'), '是否有数据': has_data, '层级': response.meta.get('parent')}
            for wd in wds:
                wd_name = name_dict.get(wd.get('wdcode'))
                w = wd_dict.get(wd.get('wdcode')).get(wd.get('valuecode'))
                w_name = w.get('cname')
                w_code = w.get('code')
                w_unit = w.get('unit')
                item_dict.update({wd_name: w_name, '{}单位'.format(wd_name): w_unit, '{}代码'.format(wd_name): w_code})
            gov_item = StatsgovItem()
            gov_item['write_data'] = item_dict.copy()
            print(item_dict)
            yield gov_item

    def func_pass(self, response):
        pass
