# -*- coding: utf-8 -*-
import json
import scrapy
import time
import logging

from chace_css.ChaCeWang.ChaCeWang.spiders.chace_tools import SpiderCha
from chace_css.ChaCeWang.ChaCeWang.items import ChacewangItem
from chace_css.ChaCeWang.ChaCeWang.settings import HEADERS, COOKIES, SAVE_PATH
from chace_css.ChaCeWang.ChaCeWang.spiders.tess import TessOcr

logging.basicConfig(level=logging.INFO, filename=SAVE_PATH.format('log'))
logger = logging.getLogger(__name__)


class ChaceSpider(scrapy.Spider):
    name = 'chace'
    allowed_domains = ['chacewang.com']
    base_url = f'http://www.chacewang.com/ProjectSearch/FindWithPager?sortField=CreateDateTime&sortOrder=desc&' \
               'pageindex={index}&pageSize=50&cylb=&diqu={area_code}&bumen=&cylbName=&partition={partition}&' \
               'partitionName={partition_name}&searchKey='
    sc = SpiderCha()
    TOcr = TessOcr()

    def start_requests(self):
        # need_area = ['天河区', '南山区', '福田区', '朝阳区', '浦东新区', '江干区']
        need_area = ['荔湾区', '番禺区', '黄埔区（开发区）', '白云区', '海珠区', '越秀区',
                     '南沙区', '花都区', '增城区', '从化区']
        city_code = self.sc.city_code('name')
        for area_name in need_area:
            area_code = city_code.get(area_name).get('area')
            city_name = city_code.get(area_name).get('city')  # 城市中文名
            for k, v in self.sc.project_type.items():
                info = {'index': 0, 'area_code': area_code,
                        'partition': k, 'partition_name': v, 'partition_real': self.sc.change(v)}
                url = self.base_url.format(**info)
                meta = {'save': {'city': city_name, 'area_name': area_name, 'info': info}}
                yield scrapy.Request(url, callback=self.parse, meta=meta, headers=HEADERS, cookies=COOKIES)
                time.sleep(1)

    def parse(self, response: scrapy.http.Response):
        req_data = json.loads(response.body.decode())
        if req_data.get('Code') == 'WebCrawlerCheckCount':
            print('===' * 20)
            logger.info('url: {} \n请求失败， 请输入验证码'.format(response.url))
            self.TOcr.do()
            print('===' * 20)
            time.sleep(10)
            yield scrapy.Request(response.url, callback=self.parse, meta={'save': response.meta.get('save')},
                                 headers=HEADERS, cookies=COOKIES, dont_filter=True)
        else:
            meta = {'save': response.meta.get('save')}
            for each in req_data.get('rows'):
                main_id = each.get('MainID')
                url = 'http://www.chacewang.com/ProjectSearch/NewPeDetail/{}?from=home'.format(main_id)
                yield scrapy.Request(url, callback=self.page, meta=meta, dont_filter=True)
            total = int(req_data.get('total'))
            index = int(req_data.get('pageIndex'))
            if (index + 1) * 50 < total:
                info = meta['save'].get('info').copy()
                info.update({'index': index + 1})
                url = self.base_url.format(**info)
                new_meta = {'save': {'city': meta['save'].get('city'),
                                     'area_name': meta['save'].get('area_name'),
                                     'info': info}}
                yield scrapy.Request(url, callback=self.parse, meta=new_meta,
                                     headers=HEADERS, cookies=COOKIES, dont_filter=True)

    def page(self, response: scrapy.http.Response):
        result = self.sc.page_detail(response)
        item = ChacewangItem()
        item['save'] = response.meta.get('save')
        item['result'] = result
        yield item


