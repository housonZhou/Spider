# -*- coding: utf-8 -*-
import re
import scrapy
from policy.ShanghaiGov.ShanghaiGov.items import ShanghaigovItem


class ShanghaiSpider(scrapy.Spider):
    name = 'shanghai'
    host = 'http://ss.shanghai.gov.cn/'
    allowed_domains = ['shanghai.gov.cn']
    base_url = 'http://ss.shanghai.gov.cn/search?q=%E6%8B%9B%E5%95%86&page={}&view=xxgk&contentScope=2&dateOrder=1&' \
               'tr=1&dr=&format=1&re=2&all=2&siteId=www.shanghai.gov.cn'
    STOP_NUM = 29

    def start_requests(self):
        for i in range(1, self.STOP_NUM):
            url = self.base_url.format(i)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for item in response.xpath('//*[@id="results"]/div'):
            url = self.host + item.xpath('a/@href').extract_first()
            time_map = item.xpath('div/div[1]/font/text()').extract_first()
            print(url, time_map)
            yield scrapy.Request(url, callback=self.page_detail, meta={'time_map': time_map})

    def page_detail(self, response):
        this_style = response.xpath('//*[@id="ivs_title"]')
        if this_style:
            result = self.style_A(response)
        else:
            result = self.style_B(response)
        item = ShanghaigovItem()
        item['time_map'] = response.meta.get('time_map')
        for k, v in result.items():
            item[k] = v
        if not item['content']:
            print('==' * 20, 'no content :', response.url)
        return item

    def style_A(self, response):
        title = response.xpath('//*[@id="ivs_title"]/text()').extract_first().strip()
        # time_map = response.xpath('//*[@id="ivs_date"]/text()').extract_first()
        # if time_map:
        #     time_map = re.findall('\d{4}\D\d{1,2}\D\d{1,2}\D{0,1}', time_map)
        content = response.xpath('string(//div[@class="Article_content"])').extract_first().strip()
        if not content:
            content = response.xpath('string(//*[@id="ivs_content"])').extract_first().strip()
        return {'title': title, 'url': response.url, 'content': content}

    def style_B(self, response):
        title = response.xpath('//div[@class="border-red"]/dl[1]/dd/text()').extract_first().strip()
        # time_map = response.xpath('//div[@class="border-red"]/div[1]/dl[2]/dd/text()').extract_first()
        content = response.xpath('string(//*[@id="ivs_content"])').extract_first().strip()
        return {'title': title, 'url': response.url, 'content': content}
