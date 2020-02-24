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


class ShangHaiWjwSpider(scrapy.Spider):
    name = 'ShangHaiWjwSpider'
    # allowed_domains = ['hubei.gov.cn']

    def start_requests(self):
        self.cookies = get_cookie('http://wsjkw.sh.gov.cn/yqtb/index.html')
        urls = [
            ("上海市-卫健委-疫情通报", "http://wsjkw.sh.gov.cn/yqtb/index.html"),
            ("上海市-卫健委-防控动态", "http://wsjkw.sh.gov.cn/fkdt/index.html"),
            ("上海市-卫健委-防控知识", "http://wsjkw.sh.gov.cn/fkzs/index.html"),
            ("上海市-卫健委-新闻发布会", "http://wsjkw.sh.gov.cn/xwfbh/index.html"),
        ]

        for name, url in urls:
            yield scrapy.Request(url, meta={"website": name, 'limit': ''},
                                 callback=self.parse_sh, headers=HEADERS, cookies=self.cookies)

    def parse_sh(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = response.meta.get('limit')
        tag = website.split('-')[-1]
        # createPageHTML(46, 0, "index", "html");
        page = SHPageControl(response)
        next_page = page.next_page()
        for item in response.xpath('//ul[@class="uli16 nowrapli list-date "]/li'):
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
            yield scrapy.Request(url, callback=self.sh_detail, headers=HEADERS, meta=meta, cookies=self.cookies)

        if next_page:
            meta = {'website': response.meta.get('website'), 'limit': limit}
            yield scrapy.Request(next_page, callback=self.parse_sh, headers=HEADERS, meta=meta, cookies=self.cookies)

    def sh_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('//div[@class="Article"]/h2[1]/text()').extract_first().strip()
        other = response.xpath('string(//*[@id="ivs_date"])').extract_first()
        pub_time = time_map(other)
        source = '上海发布'
        # pub_dept = obj_first(re.findall(r'发布机构：\s*([^\s|]*)\s*', other))
        # if not source and pub_dept:
        #     source = pub_dept
        # 正文识别区
        content_xpath = '//*[@id="ivs_content"]'
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


class SHPageControl:
    """
    翻页器： $(".pagination").pagination("setPage",6,6);
             http://wsjkw.sh.gov.cn/yqtb/index_6.html
    """
    def __init__(self, response: scrapy.http.Response):
        # createPageHTML(89, 1,"index", "shtml",  "black2",621);
        self.find = re.findall(r'totalPage: (\d+),', response.text)
        self.total = int(obj_first(self.find, error='0'))
        self.url = response.url
        now = obj_first(re.findall(r'index_(\d+).html', self.url), error='1')
        self.next = int(now)

    def next_page(self):
        if self.total > self.next:
            base_url = self.url.split('/')
            base_url[-1] = '{}_{}.{}'.format('index', self.next + 1, "html")
            return '/'.join(base_url)
        else:
            return None
