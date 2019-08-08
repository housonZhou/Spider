# -*- coding: utf-8 -*-
import scrapy
import re
from lxml.etree import HTML
from policy.HangzhouGov.HangzhouGov.items import HangzhougovItem


class HangzhouSpider(scrapy.Spider):
    name = 'hangzhou'
    allowed_domains = ['hangzhou.gov.cn']
    base_url = 'http://tzcj.hangzhou.gov.cn'
    start_urls = ['http://tzcj.hangzhou.gov.cn/col/col1603992/index.html?uid=4853043&pageNum=1']

    def parse(self, response):
        html_str = response.xpath('string(//*[@id="4853043"])').extract_first()
        item_list = re.findall('<li>.*?</li>', html_str)
        for item in item_list:
            tree = HTML(item)
            time_map = tree.xpath('//span/text()')[0]
            link = tree.xpath('//a/@href')[0]
            url = self.base_url + link
            yield scrapy.Request(url, callback=self.page_detail, meta={'time_map': time_map})

    def page_detail(self, response):
        item = HangzhougovItem()
        item['time_map'] = response.meta.get('time_map')
        item['title'] = response.xpath('//div[@class="tz_xl_title"]/text()').extract_first().strip()
        item['content'] = response.xpath('string(//*[@id="zoom"])').extract_first().strip()
        item['url'] = response.url
        return item
