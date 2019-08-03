# -*- coding: utf-8 -*-
import scrapy
import json
from urllib import parse
from traffic_sz.chinadaily.chinadaily.settings import SEARCH_LIST
from traffic_sz.chinadaily.chinadaily.items import ChinadailyItem


class ChinadailySpider(scrapy.Spider):
    name = 'ChinaDaily'
    allowed_domains = ['newssearch.chinadaily.com.cn']
    base_url = 'http://newssearch.chinadaily.com.cn/rest/cn/search?'

    def start_requests(self):
        for key_word in SEARCH_LIST:
            data = {'fullMust': key_word, 'fullAny': key_word, 'sort': "dp", 'duplication': 'off', 'page': '0'}
            url = self.base_url + parse.urlencode(data)
            print('start url :', url)
            yield scrapy.Request(url, method='GET', callback=self.parse)

    def url_decode(self, url):
        params = url.split('?')
        if len(params) == 1:
            return {}
        params = params[-1]
        params_data = {}
        for item in params.split('&'):
            params_data[item.split('=')[0]] = parse.unquote(item.split('=')[-1])
        return params_data

    def parse(self, response):
        params_data = self.url_decode(response.url)
        data = response.body.decode()
        data = json.loads(data)
        now_number = data.get('number')
        total_pages = data.get('totalPages')
        content_data = data.get('content')
        for item in content_data:
            items = ChinadailyItem()
            items['inner_id'] = item.get('inner_id')
            items['title'] = item.get('title')
            items['source'] = item.get('source')
            items['url'] = item.get('url')
            items['content'] = item.get('plainText')
            keywords = item.get('keywords')
            items['key_word'] = json.dumps(keywords[: 5] if len(keywords) > 5 else keywords, ensure_ascii=False)
            items['time_map'] = item.get('pubDateStr')
            items['search_word'] = params_data.get('fullMust')
            yield items
        print(now_number, total_pages, params_data)
        if now_number < total_pages:
            params_data.update({'page': str(now_number + 1)})
            next_url = self.base_url + parse.urlencode(params_data)
            yield scrapy.Request(next_url, method='GET', callback=self.parse)
