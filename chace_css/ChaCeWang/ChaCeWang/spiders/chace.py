# -*- coding: utf-8 -*-
import copy
import json
import time

import scrapy

from chace_css.ChaCeWang.ChaCeWang.items import ChacewangItem
from chace_css.ChaCeWang.ChaCeWang.settings import HEADERS, COOKIES
from chace_css.ChaCeWang.ChaCeWang.spiders.chace_tools import SpiderCha
from chace_css.ChaCeWang.ChaCeWang.spiders.tess import TessOcr, Login


class ChaceSpider(scrapy.Spider):
    name = 'chace'
    allowed_domains = ['chacewang.com']
    base_url = f'http://www.chacewang.com/ProjectSearch/FindWithPager?sortField=CreateDateTime&sortOrder=desc&' \
               'pageindex={index}&pageSize=50&cylb=&diqu={area_code}&bumen=&cylbName=&partition={partition}&' \
               'partitionName={partition_name}&searchKey='
    sc = SpiderCha()
    TOcr = TessOcr()
    Lg = Login()

    def start_requests(self):
        # need_area = ['天河区', '南山区', '福田区', '朝阳区', '浦东新区', '江干区']
        # need_area = ['富阳区', '建德市', '淳安县', '桐庐县', '余杭区', '萧山区', '杭州国家高新技术产业开发区（滨江）',
        #              '西湖区', '拱墅区', '下城区', '上城区', '临安区', '钱塘新区', '杭州钱江经济开发区']
        need_area = ['广州', '北京', '上海', '杭州市']
        city_code = self.sc.city_code('name')
        for area_name in need_area:
            area_code = city_code.get(area_name).get('area')
            city_name = city_code.get(area_name).get('city')  # 城市中文名
            for k, v in self.sc.project_type.items():
                info = {'index': 0, 'area_code': area_code,
                        'partition': k, 'partition_name': v, 'partition_real': self.sc.change(v)}
                url = self.base_url.format(**info)
                meta = {'save': {'city': city_name, 'area_name': area_name, 'info': info}}
                yield scrapy.Request(url, callback=self.parse, meta=copy.deepcopy(meta),
                                     headers=HEADERS, cookies=COOKIES)
                time.sleep(1)

    def parse(self, response: scrapy.http.Response):
        time.sleep(1)
        req_data = json.loads(response.body.decode())
        save = copy.deepcopy(response.meta.get('save'))
        if req_data.get('Code') == 'WebCrawlerCheckCount':
            print('===' * 20)
            print('url: {} \n请求失败， 请输入验证码'.format(response.url))
            self.TOcr.do()
            yield scrapy.Request(response.url, callback=self.parse, meta={'save': save},
                                 headers=HEADERS, cookies=COOKIES, dont_filter=True)
        elif req_data.get('Code') == 'WebCrawlerCheckPage':
            print('===' * 20)
            print('登录超时')
            self.Lg.do()
            yield scrapy.Request(response.url, callback=self.parse, meta={'save': save},
                                 headers=HEADERS, cookies=COOKIES, dont_filter=True)
        else:
            meta = {'save': save}
            for each in req_data.get('rows'):
                main_id = each.get('MainID')
                default_area = each.get('AreaFullName')
                meta_ = meta.copy()
                meta_['save']['default_area'] = self.sc.change(default_area)
                meta_['save']['MainID'] = main_id
                url = 'http://www.chacewang.com/ProjectSearch/NewPeDetail/{}?from=home'.format(main_id)
                yield scrapy.Request(url, callback=self.page, meta=copy.deepcopy(meta_), dont_filter=True)
            total = int(req_data.get('total'))
            index = int(req_data.get('pageIndex'))
            if (index + 1) * 50 < total:
                info = meta['save'].get('info').copy()
                info.update({'index': index + 1})
                url = self.base_url.format(**info)
                new_meta = {'save': {'city': meta['save'].get('city'),
                                     'area_name': meta['save'].get('area_name'),
                                     'info': info}}
                time.sleep(1)
                yield scrapy.Request(url, callback=self.parse, meta=copy.deepcopy(new_meta),
                                     headers=HEADERS, cookies=COOKIES, dont_filter=True)

    def page(self, response: scrapy.http.Response):
        time.sleep(1)
        result = self.sc.page_detail(response)
        item = ChacewangItem()
        item['save'] = response.meta.get('save')
        item['result'] = result
        print(item['save'])
        yield item


