# -*- coding: utf-8 -*-
import re
import scrapy
from scrapy import log
from lxml.etree import HTML
from traffic_sz.SzNews.SzNews.items import SznewsItem
from traffic_sz.SzNews.SzNews.settings import SEARCH_LIST, BAIDU_COOKIES

TIME_MAP = re.compile("\d{4}\D\d{2}\D\d{2}")


class SznewsSpider(scrapy.Spider):
    name = 'sznews'
    allowed_domains = ['sznews.com', 'baidu.com']
    baidu_url = 'http://www.baidu.com'
    base_url = 'http://www.baidu.com/s?ie=utf-8&mod=1&isbd=1&isid=9f53d780000145d7&wd=site%3A(www.sznews.com)%20{}&pn=0'

    def start_requests(self):
        for word in SEARCH_LIST:
            url = self.base_url.format(word)
            yield scrapy.Request(url, callback=self.parse, meta={'q': word}, cookies=BAIDU_COOKIES)

    def parse(self, response):
        page_list = response.xpath('//*[@id="content_left"]/div[@class="result c-container "]/h3/a/@href').extract()
        for link in page_list:
            yield scrapy.Request(link, callback=self.page_detail, meta=response.meta)
        page_next = response.xpath('//*[@id="page"]/a[last()]/text()').extract_first()
        if not page_next:
            print(response.text)
        if '下一页' in page_next:
            link_next = response.xpath('//*[@id="page"]/a[last()]/@href').extract_first()
            link_next = self.baidu_url + link_next
            yield scrapy.Request(link_next, callback=self.parse, meta=response.meta)

    def page_detail(self, response: scrapy.http.Response):
        item = SznewsItem()
        item['url'] = response.url
        item['search_word'] = response.meta.get('q')
        item['title'] = response.xpath('string(//h1)').extract_first().strip()
        this_style = response.xpath('//*[@id="inner"]')
        if this_style:
            item.update(style_inner(response))
        else:
            item.update(style_out(response))
        if item['content']:
            yield item
        else:
            print('==' * 10, 'url not content :  ', response.url)


def style_inner(response: scrapy.http.Response):
    item = dict()
    detail = response.xpath('string(//div[@class="origin"])').extract_first()
    time_map = TIME_MAP.findall(detail)
    if not time_map:
        time_map = TIME_MAP.findall(response.url)
    source = re.findall('来源：(.*)', detail)
    item['source'] = source[0] if source else '深圳新闻网'
    item['content'] = get_content(response.text, inner=True)
    item['time_map'] = time_map[0].replace('/', '-')
    return item


def style_out(response: scrapy.http.Response):
    item = dict()
    detail = response.xpath('string(//div[contains(@class,"fs18")])').extract_first()
    time_map = TIME_MAP.findall(detail)
    if not time_map:
        time_map = TIME_MAP.findall(response.url)
    source = re.findall('来源：(.*)', detail)
    item['source'] = source[0] if source else '深圳新闻网'
    item['content'] = get_content(response.text)
    item['time_map'] = time_map[0].replace('/', '-')
    return item


def get_content(response: str, inner=False):
    try:
        tree = HTML(response)
        if inner:
            xpath_str = '//div[contains(@class, "artical-con")]'
        else:
            xpath_str = '//div[contains(@class, "article-content") or contains(@class, "new_txt")]'
        content = tree.xpath(xpath_str)[0]
        for dom in content.xpath('//script'):
            new_content = dom.getparent()
            new_content.remove(dom)
        return content.xpath('string(.)').strip()
    except Exception as e:
        print(e)
        return
