# -*- coding: utf-8 -*-
import scrapy
from .load_tree import *
from BaiKe.items import BaikeItem
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class BaikeSpider(CrawlSpider):
    name = 'baike'
    allowed_domains = ['baike.baidu.com']
    start_urls = ['https://baike.baidu.com/item/%E8%85%BE%E8%AE%AF/112204']
    rules = [Rule(LinkExtractor(allow=("item/.+", ), deny=("item/.+?\#.+", )), callback="baike_parse", follow=True)]

    def baike_parse(self, response):
        item = BaikeItem()
        url = response.request.url
        page_data = base_msg(response)
        if page_data.get("tag"):
            item["url"] = url
            for k, v in page_data.items():
                item[k] = v
            yield item
