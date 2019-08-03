# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ChinadailyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    inner_id = scrapy.Field()
    title = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()
    content = scrapy.Field()
    key_word = scrapy.Field()
    time_map = scrapy.Field()
    search_word = scrapy.Field()
    pass
