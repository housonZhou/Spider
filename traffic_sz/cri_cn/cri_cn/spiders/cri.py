# -*- coding: utf-8 -*-
import scrapy
from traffic_sz.cri_cn.cri_cn.settings import SEARCH_LIST


class CriSpider(scrapy.Spider):
    name = 'cri'
    allowed_domains = ['cri.cn', 'baidu.com']
    base_url = 'http://www.baidu.com/s?wd=site%3A(cri.cn)%20{}&pn=0&ie=utf-8'

    def start_requests(self):
        for word in SEARCH_LIST:
            url = self.base_url.format(word)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response: scrapy.http.response.Response):
        # page_list = response.xpath('//*[@id="content_left"]/div[@class="result c-container "]/h3/a/@href').extract()
        # for link in page_list:
        #     yield scrapy.Request(link, callback=self.cri_page)
        page_next = response.xpath('//*[@id="page"]/a[last()]/text()').extract_first()
        print(page_next)
        if not page_next:
            print(response.body.decode())
        # print(response.body.decode())
        if page_next == '下一页>':
            print('next')
            next_link = response.xpath('//*[@id="page"]/a[last()]/@href').extract_first()
            yield scrapy.Request('http://www.baidu.com{}'.format(next_link), callback=self.parse)

    def cri_page(self, response: scrapy.http.response.Response):
        pass
