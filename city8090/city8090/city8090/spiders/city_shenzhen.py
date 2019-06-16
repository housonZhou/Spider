# -*- coding: utf-8 -*-
import scrapy


class CityShenzhenSpider(scrapy.Spider):
    name = 'city_shenzhen'
    allowed_domains = ['life.city8090.com']
    start_urls = ['http://life.city8090.com/']

    def parse(self, response):
        pass
