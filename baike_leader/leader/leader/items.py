# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class LeaderItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    subtitle = scrapy.Field()
    url = scrapy.Field()
    summary = scrapy.Field()
    time_resume = scrapy.Field()
    info = scrapy.Field()
