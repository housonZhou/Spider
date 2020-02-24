# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ArticleItem(scrapy.Item):
    article_id = scrapy.Field()
    title = scrapy.Field()
    tag = scrapy.Field()
    website = scrapy.Field()
    url = scrapy.Field()
    pub_time = scrapy.Field()
    source = scrapy.Field()
    content = scrapy.Field()
    image_url = scrapy.Field()
    attachment = scrapy.Field()
    html_content = scrapy.Field()


class PressItem(scrapy.Item):
    article_id = scrapy.Field()
    title = scrapy.Field()
    tag = scrapy.Field()
    website = scrapy.Field()
    url = scrapy.Field()
    pub_time = scrapy.Field()
    content = scrapy.Field()
    image_url = scrapy.Field()
    state = scrapy.Field()
    location = scrapy.Field()
    guest = scrapy.Field()
    abstract = scrapy.Field()
    html_content = scrapy.Field()


class ZhengcekuItem(scrapy.Item):
    source = scrapy.Field()
    file_type = scrapy.Field()
    cate = scrapy.Field()
    pub_dept = scrapy.Field()
    write_date = scrapy.Field()
    pub_date = scrapy.Field()
    content = scrapy.Field()
    title = scrapy.Field()
    pub_no = scrapy.Field()
    tag = scrapy.Field()
    website = scrapy.Field()
    url = scrapy.Field()
    article_id = scrapy.Field()
    attachment = scrapy.Field()
    html_content = scrapy.Field()
    is_effective = scrapy.Field()
    effective_start = scrapy.Field()
    effective_end = scrapy.Field()
    theme_word = scrapy.Field()
    industry = scrapy.Field()


class ZhengceContentItem(scrapy.Item):
    index_no = scrapy.Field()
    cate = scrapy.Field()
    pub_dept = scrapy.Field()
    write_date = scrapy.Field()
    pub_date = scrapy.Field()
    content = scrapy.Field()
    title = scrapy.Field()
    pub_no = scrapy.Field()
    tag = scrapy.Field()
    website = scrapy.Field()
    url = scrapy.Field()
    article_id = scrapy.Field()
    attachment = scrapy.Field()
    industry = scrapy.Field()
    theme_word = scrapy.Field()
    html_content = scrapy.Field()
    is_effective = scrapy.Field()
    effective_start = scrapy.Field()
    effective_end = scrapy.Field()
