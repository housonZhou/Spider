# -*- coding: utf-8 -*-
import re
import scrapy
from policy.GuanzhouGov.GuanzhouGov.items import GuanzhougovItem


class GuanzhouSpider(scrapy.Spider):
    name = 'guanzhou'
    base_url = 'http://so.gz.gov.cn/'
    allowed_domains = ['gz.gov.cn']

    def start_requests(self):
        for i in range(1, 10):
            url = 'http://so.gz.gov.cn/s?q=1&qt=%E6%8B%9B%E5%95%86%E5%BC%95%E8%B5%84&paging=1&pageSize=10&' \
                  'sort=dateDesc&database=zc&siteCode=gzgov&docQt=&page={}'.format(i)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for item in response.xpath('//div[@class="msg discuss"]'):
            link = item.xpath('div[1]//a/@href').extract_first()
            url = self.base_url + link
            time_map = item.xpath('div[2]/span/text()').extract_first()
            yield scrapy.Request(url, callback=self.change_url, meta={'time_map': time_map})

    def change_url(self, response):
        data = response.text
        real_url = re.findall('location.href = "(.*?)"', data)[0]
        yield scrapy.Request(real_url, callback=self.page_detail, meta={'time_map': response.meta.get('time_map')})

    def page_detail(self, response):
        item = GuanzhougovItem()
        item['url'] = response.url
        item['time_map'] = response.meta.get('time_map')
        item['title'] = response.xpath('//h1[@class="content_title"]/text()').extract_first().strip()
        item['content'] = response.xpath('string(//*[@id="zoomcon"])').extract_first().strip()
        print(item)
        return item
