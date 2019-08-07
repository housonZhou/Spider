# -*- coding: utf-8 -*-
import re
import scrapy
from fake_useragent import UserAgent
from lxml.etree import HTML
from traffic_sz.ChinaNews.ChinaNews.settings import SEARCH_LIST, POST_DATA, END_SEARCH_TIME
from traffic_sz.ChinaNews.ChinaNews.items import ChinanewsItem


class ChinaNewsSpider(scrapy.Spider):
    name = 'china_news'
    allowed_domains = ['chinanews.com']
    base_url = 'http://sou.chinanews.com/search.do'
    ua = UserAgent()

    def start_requests(self):
        for word in SEARCH_LIST:
            data = POST_DATA.copy()
            data['q'] = word
            print(data)
            yield scrapy.FormRequest(self.base_url, method='POST', formdata=data, callback=self.parse, meta={'q': word})

    def parse(self, response: scrapy.http.Response):
        q = response.meta['q']
        have_next = True
        page_link = response.xpath('//ul[@class="news_item"]/li[@class="news_title"]/a/@href').extract()
        time_list = response.xpath('//ul[@class="news_item"]/li[@class="news_other"]/text()').extract()
        for i in range(len(page_link)):
            time_map = re.findall('\d{4}-\d{2}-\d{2}', time_list[i])
            if time_map and time_map[0] > END_SEARCH_TIME:
                yield scrapy.Request(page_link[i], callback=self.page_detail, meta={'q': q})
            elif time_map and time_map[0] <= END_SEARCH_TIME:
                have_next = False
                break
        next_data = self.get_next(response)
        if next_data and have_next:
            data = POST_DATA.copy()
            data['q'] = q
            data['start'] = str(next_data * 100)
            yield scrapy.FormRequest(self.base_url, method='POST', formdata=data, callback=self.parse, meta={'q': q})

    def page_detail(self, response: scrapy.http.Response):
        item = ChinanewsItem()
        item['url'] = response.url
        item['search_word'] = response.meta['q']
        item['content'] = self.get_content(response.text)
        item['title'] = response.xpath('//h1/text()').extract_first().strip()
        left = response.xpath('//div[@class="left-t"]/text()').extract()
        if not left:
            left = response.xpath('//div[@class="left_time"]/text()').extract()
        item['time_map'] = re.findall('\d{4}\D\d{1,2}\D\d{1,2}\D', left[0])[0]
        item['source'] = re.findall('来源：(.*)', left[0])[0].strip()
        return item

    def get_content(self, response):
        tree = HTML(response)
        content = tree.xpath('//div[@class="left_zw"]')[0]
        for dom in content.xpath('//script'):
            new_content = dom.getparent()
            new_content.remove(dom)
        return content.xpath('string(.)').strip()

    def get_next(self, response):
        page_next = response.xpath('//*[@id="pagediv"]/*[last()-1]/text()').extract_first()
        if page_next == '下一页':
            next_link = response.xpath('//*[@id="pagediv"]/*[last()-1]').extract()
            if next_link:
                next_link = re.findall('\d+', next_link[0])
                if next_link:
                    return int(next_link[0])
        return
