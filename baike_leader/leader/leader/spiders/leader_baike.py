# -*- coding: utf-8 -*-
import re
import json
import logging

import scrapy
import pandas as pd
from lxml.etree import HTML

from baike_leader.leader.leader.settings import START_EXCEL, LOG_PATH
from baike_leader.leader.leader.items import LeaderItem


logging.basicConfig(level=logging.DEBUG, filename=LOG_PATH)
logger = logging.getLogger(__name__)


class LeaderBaikeSpider(scrapy.Spider):
    name = 'leader_baike'
    allowed_domains = ['baidu.com']
    df = pd.read_excel(START_EXCEL)
    start_data = df.to_dict(orient='records')

    def start_requests(self):
        for item in self.start_data:
            name = item.get('领导姓名')
            name = re.sub('\s', '', name)
            item['领导姓名'] = name
            job = item.get('职务')
            belong = item.get('所属机构')
            # 防止搜索关键词超过长度限制：38
            out = (belong if len(belong) < len(job) else job) if len(belong) + len(job) > 28 else ''.join([belong, job])
            url = 'http://www.baidu.com/s?ie=utf-8&wd={} {} 百度百科'.format(out, name)
            logger.info('crawl this url: {}'.format(url))
            yield scrapy.Request(url, meta={'item': item}, callback=self.parse)

    def parse(self, response: scrapy.http.Response):
        for each in response.xpath('//*[@id="content_left"]/div/h3/a'):
            title = each.xpath('string(.)').extract_first()
            link = each.xpath('@href').extract_first()
            if '百度百科' in title and response.meta.get('item').get('领导姓名') in title:
                yield scrapy.Request(link, meta={'item': response.meta['item']}, callback=self.detail)
                break
        else:
            city = response.meta.get('item').get('城市')
            name = response.meta.get('item').get('领导姓名')
            key_word = '{} {} 百度百科'.format(city, name)
            if key_word != response.xpath('//*[@id="kw"]/@value').extract_first():
                new_url = 'http://www.baidu.com/s?ie=utf-8&wd={}'.format(key_word)
                yield scrapy.Request(new_url, meta={'item': response.meta['item']}, callback=self.parse)
            else:
                logger.info('no data: {}'.format(response.meta.get('item')))
                item = LeaderItem()
                item.update({'title': '', 'subtitle': '', 'summary': '', 'url': '', 'info':  response.meta.get('item')})
                yield item

    def detail(self, response: scrapy.http.Response):
        item = LeaderItem()
        msg = response.xpath('//div[@class="main-content"]/div[@class="para"]').extract()
        item['title'] = response.xpath('//h1/text()').extract_first()
        subtitle = response.xpath('//h1/following-sibling::h2/text()').extract_first()
        item['subtitle'] = subtitle if subtitle else ''

        lemma_summary = response.xpath('//div[@class="lemma-summary"]')
        lemma_summary = lemma_summary[0] if lemma_summary else ''
        item['summary'] = lemma_summary.xpath('string(.)').extract_first().strip() if lemma_summary else ''
        time_resume = self.get_time_from_str(msg)
        item['url'] = response.url
        item['time_resume'] = json.dumps(time_resume, ensure_ascii=False)
        item['info'] = response.meta.get('item')
        yield item

    @staticmethod
    def get_time_from_str(xpath_list) -> list:
        dd = []
        for each in xpath_list:
            tree = HTML(re.sub('\<br.*?\>', '\n', each))
            line_all = tree.xpath('string(.)')
            for line in line_all.split('\n'):
                result = re.match(r'^\s*(\d{4})(\D([1-9]|0[1-9]|1[0-2])|)\D', line)
                if result:
                    y, _, m = result.groups()
                    time_map = [y, '{:0>2d}'.format(int(m))] if m else [y]
                    dd.append({'time': '.'.join(time_map), 'do': line.strip()})
        return dd

