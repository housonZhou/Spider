# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BaikeItem(scrapy.Item):
    # define the fields for your item here like:
    word_name = scrapy.Field()
    word_msg = scrapy.Field()
    same_name = scrapy.Field()
    tag = scrapy.Field()
    tag_list = scrapy.Field()
    basic_info = scrapy.Field()
    summary = scrapy.Field()
    url = scrapy.Field()
    level_1 = scrapy.Field()
    level_2 = scrapy.Field()
    pass
