# -*- coding: utf-8 -*-
import hashlib
import re
from urllib.parse import urljoin

import redis
import scrapy
from article.items import ArticleItem, ZhengcekuItem, ZhengceContentItem
from article.util import get_cookie, obj_first, get_html_content, time_map, xpath_from_remove, PageHTMLControl
from article.settings import HEADERS
from lxml.etree import HTML

m = hashlib.md5()
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
conn = redis.StrictRedis(connection_pool=pool)


class WuHanGovSpider(scrapy.Spider):
    name = 'WuHanGovSpider'
    # allowed_domains = ['hubei.gov.cn']

    def start_requests(self):
        # self.cookies_hb = get_cookie('http://fgw.hubei.gov.cn/fbjd/tzgg/tz/')
        limit = '2020-01-23'

        url = 'http://www.wuhan.gov.cn/hbgovinfo/zwgk_8265/tzgg/'
        name = '武汉市-人民政府-通知公告'
        yield scrapy.Request(url, meta={"website": name, 'limit': limit},
                             callback=self.parse_wh, headers=HEADERS)

        gf_url = 'http://www.wuhan.gov.cn/hbgovinfo/zwgk_8265/szfxxgkml/fggw/gfxwj/'
        name = '武汉市-人民政府-规范性文件'
        yield scrapy.Request(gf_url, meta={"website": name, 'limit': limit},
                             callback=self.parse_gf, headers=HEADERS)

    def parse_wh(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = response.meta.get('limit')
        tag = website.split('-')[-1]
        # createPageHTML(46, 0, "index", "html");
        page = PageHTMLControl(response.text, 'createPageHTML(.*?);')
        next_page = page.next_page(response.url)
        for item in response.xpath('//ul[@class="list"]/li'):
            link = item.xpath('./a/@href').extract_first()
            url = urljoin(response.url, link)
            if limit:
                time_ = time_map(item.xpath('./span/text()').extract_first())
                if time_ < limit:
                    next_page = None
                    continue
            # if ('beijing.gov.cn' not in url) or ('video' in url) or ('pdf' in url):
            #     continue
            conn.hset("bf", tag + '-' + url, 1)
            meta = {'tag': tag, 'website': website}
            # print(meta, url)
            yield scrapy.Request(url, callback=self.wh_detail, headers=HEADERS, meta=meta)

        if next_page:
            meta = {'website': response.meta.get('website'), 'limit': limit}
            yield scrapy.Request(next_page, callback=self.parse_wh, headers=HEADERS, meta=meta)

    def wh_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//h1)').extract_first().strip()
        other = response.xpath('string(//ul[@class="fl"])').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：\s*(\S*)', other))
        # pub_dept = obj_first(re.findall(r'发布机构：\s*([^\s|]*)\s*', other))
        # if not source and pub_dept:
        #     source = pub_dept
        # 正文识别区
        content_xpath = '//*[@id="zoomcon"]'
        content = xpath_from_remove(response, 'string({})'.format(content_xpath))
        # content = response.xpath('string({})'.format(content_xpath)).extract_first().strip()
        html_content = get_html_content(response, content_xpath)
        image_url = response.xpath('{}//img/@src'.format(content_xpath)).extract()
        image_url = [urljoin(response.url, i) for i in image_url]
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_xpath))
        attachment = []
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = urljoin(response.url, url_)
            attachment.append((file_name, download_url))

        item = ArticleItem()
        item["title"] = title
        item["pub_time"] = pub_time
        item["source"] = source
        item["content"] = content
        item["image_url"] = image_url
        item["attachment"] = attachment
        item["html_content"] = html_content
        item["tag"] = response.meta.get('tag')
        item["website"] = response.meta.get('website')
        item["url"] = response.url
        item["article_id"] = article_id
        # print(item)
        yield item

    def parse_gf(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = response.meta.get('limit')
        tag = website.split('-')[-1]
        # createPageHTML(46, 0, "index", "html");
        page_text = response.xpath('string(//*[@id="list_navigator"])').extract_first()
        page = PageHTMLControl(page_text, 'createPageHTML(.*?);')
        next_page = page.next_page(response.url)
        for item in response.xpath('//table[@class="publiclisttable"]/tr'):
            link = item.xpath('./td[1]/a/@href').extract_first()
            url = urljoin(response.url, link)
            if limit:
                time_ = time_map(item.xpath('./td[3]/text()').extract_first())
                if time_ < limit:
                    next_page = None
                    continue
            # if ('beijing.gov.cn' not in url) or ('video' in url) or ('pdf' in url):
            #     continue
            conn.hset("bf", tag + '-' + url, 1)
            meta = {'tag': tag, 'website': website}
            # print(meta, url)
            yield scrapy.Request(url, callback=self.gf_detail, headers=HEADERS, meta=meta)

        if next_page:
            meta = {'website': response.meta.get('website'), 'limit': limit}
            yield scrapy.Request(next_page, callback=self.parse_gf, headers=HEADERS, meta=meta)

    def gf_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        item = ZhengceContentItem()

        item["index_no"] = response.xpath('//div[@class="zlm_con02"]/table/tbody/tr[1]/th[2]/text()').extract_first()
        item["cate"] = response.xpath('//div[@class="zlm_con02"]/table/tbody/tr[1]/th[4]/text()').extract_first()
        item["pub_dept"] = response.xpath('//div[@class="zlm_con02"]/table/tbody/tr[2]/td[2]/text()').extract_first()
        item["write_date"] = time_map(response.xpath('//div[@class="zlm_con02"]/table/tbody/tr[4]/td[2]/text()').extract_first())
        item["pub_date"] = time_map(response.xpath('//div[@class="zlm_con02"]/table/tbody/tr[3]/td[2]/text()').extract_first())
        item["pub_no"] = response.xpath('//div[@class="zlm_con02"]/table/tbody/tr[2]/td[4]/text()').extract_first()
        item["is_effective"] = response.xpath('//div[@class="zlm_con02"]/table/tbody/tr[3]/td[4]/text()').extract_first()

        content_xpath = '//*[@id="zoomcon"]'
        content = xpath_from_remove(response, 'string({})'.format(content_xpath))
        # content = response.xpath('string({})'.format(content_xpath)).extract_first().strip()
        html_content = get_html_content(response, content_xpath)
        title = response.xpath('string(//h1)').extract_first().strip()
        attach = response.xpath('{}//a'.format(content_xpath))
        attachment = []
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = urljoin(response.url, url_)
            attachment.append((file_name, download_url))
        item["content"] = content
        item["html_content"] = html_content
        item["title"] = title
        item["attachment"] = attachment
        item["tag"] = response.meta.get('tag')
        item["website"] = response.meta.get('website')
        item["url"] = response.url
        item["article_id"] = article_id
        yield item