# -*- coding: utf-8 -*-
import hashlib
import re
from urllib.parse import urljoin

import redis
import scrapy
from article.items import ArticleItem, ZhengcekuItem, ZhengceContentItem
from article.util import get_cookie, obj_first, get_html_content, time_map, xpath_from_remove, query2dict, parse2query
from article.settings import HEADERS
from lxml.etree import HTML

m = hashlib.md5()
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
conn = redis.StrictRedis(connection_pool=pool)


class GXJSpider(scrapy.Spider):
    name = 'GXJSpider'
    # allowed_domains = ['hubei.gov.cn']

    def start_requests(self):
        # self.cookies_hb = get_cookie('http://fgw.hubei.gov.cn/fbjd/tzgg/tz/')
        urls = [
            ("工信局-通知公告", "http://www.miit.gov.cn/n973401/n7647394/n7647399/index.html", self.parse_gxj, {}),
            ("深圳市-工信局-政策法规", "http://gxj.sz.gov.cn/xxgk/xxgkml/zcfgjzcjd/gygh/202002/t20200209_19005892.htm",
             self.sz_detail, {}),
            ("深圳市-工信局-政策解读", "http://gxj.sz.gov.cn/xxgk/xxgkml/zcfgjzcjd/zcjd/202002/t20200209_19005895.htm",
             self.sz_detail, {}),
            ("广州市-工信局-通知公告", "http://gxj.gz.gov.cn/yw/tzgg/index.html", self.parse_gz, {}, '2020-01-23'),
        ]
        for name, url, call, cookies, *limit in urls:
            limit = obj_first(limit)
            yield scrapy.Request(url, meta={"website": name, 'limit': limit},
                                 callback=call, headers=HEADERS, cookies=cookies)
        # 杭州市
        hz_url = 'http://jxj.hangzhou.gov.cn/module/xxgk/search.jsp?texttype=0&fbtime=-1&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage=1&sortfield=b_settop:0,createdate:0,orderid:0'
        data_str = 'infotypeId=A007A001&jdid=3244&area=&divid=div1692685&vc_title=&vc_number=&sortfield=b_settop:0,createdate:0,orderid:0&currpage=1&vc_filenumber=&vc_all=&texttype=0&fbtime=-1&texttype=0&fbtime=-1&vc_all=&vc_filenumber=&vc_title=&vc_number=&currpage=1&sortfield=b_settop:0,createdate:0,orderid:0'
        self.hz_data = query2dict('http://www.aaa.com/a?{}'.format(data_str))
        yield scrapy.FormRequest(hz_url, formdata=self.hz_data, headers=HEADERS, callback=self.parse_hz,
                                 meta={"website": "杭州市-工信局-通知文件", 'limit': "2020-01-23"})

    def parse_gxj(self, response: scrapy.http.Response):
        headers = response.request.headers
        website = response.meta.get('website')
        limit = obj_first(response.meta.get('limit'))
        tag = website.split('-')[-1]

        page = response.xpath('//div[@style="display:none"]/a/@href').extract()
        next_page = [urljoin(response.url, i) for i in page]
        for item in response.xpath('//div[@class="list center wryh14gray"]/ul/li'):
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
            yield scrapy.Request(url, callback=self.gxj_detail, headers=headers, meta=meta)

        for url in next_page:
            meta = {'website': response.meta.get('website'), 'limit': limit}
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_gxj, headers=HEADERS, meta=meta)

    def gxj_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//h2[@class="wryh18blueb center"])').extract_first().strip()
        other = response.xpath('string(//div[@class="time wryh14gray"])').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：\s*(\S*)', other))
        # pub_dept = obj_first(re.findall(r'发布机构：\s*([^\s|]*)\s*', other))
        # if not source and pub_dept:
        #     source = pub_dept
        # 正文识别区
        content_xpath = '//div[@class="center con"]'
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

    def sz_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//h1)').extract_first().strip()
        other = response.xpath('string(//h6)').extract_first()
        pub_time = time_map(other)
        source = '深圳市工业和信息化局'
        # pub_dept = obj_first(re.findall(r'发布机构：\s*([^\s|]*)\s*', other))
        # if not source and pub_dept:
        #     source = pub_dept
        # 正文识别区
        content_xpath = '//div[@class="news_cont_d_wrap"]'
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
        item["tag"] = response.meta.get('website').split('-')[-1]
        item["website"] = response.meta.get('website')
        item["url"] = response.url
        item["article_id"] = article_id
        # print(item)
        yield item

    def parse_gz(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = response.meta.get('limit')
        tag = website.split('-')[-1]

        page = response.xpath('//*[@id="page_div"]/a[@class="next"]/@href').extract_first()
        next_page = urljoin(response.url, page)
        for item in response.xpath('//ul[@class="News_list"]/li'):
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
            yield scrapy.Request(url, callback=self.gz_detail, headers=HEADERS, meta=meta)

        if next_page:
            meta = {'website': response.meta.get('website'), 'limit': limit}
            # print(url, meta)
            yield scrapy.Request(next_page, callback=self.parse_gz, headers=HEADERS, meta=meta)

    def gz_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//h1)').extract_first().strip()
        other = response.xpath('string(//div[@class="info_fbt"])').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：\s*(\S*)', other)).strip()
        if source == '本网':
            source = '广州市工业和信息化局'
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

    def parse_hz(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = response.meta.get('limit')
        tag = website.split('-')[-1]
        page = obj_first(re.findall(r'currpage=(\d+)', response.url))
        next_page = re.sub('currpage={}'.format(page), 'currpage={}'.format(int(page) + 1), response.url)
        for item in response.xpath('//li[@class="tab_box"]'):
            link = item.xpath('./a/@href').extract_first()
            url = urljoin(response.url, link)
            if limit:
                time_ = time_map(item.xpath('./a/span[@class="sub_tab_span3"]/text()').extract_first())
                if time_ < limit:
                    next_page = None
                    continue
            # if ('beijing.gov.cn' not in url) or ('video' in url) or ('pdf' in url):
            #     continue
            conn.hset("bf", tag + '-' + url, 1)
            meta = {'tag': tag, 'website': website}
            # print(meta, url)
            yield scrapy.Request(url, callback=self.hz_detail, headers=HEADERS, meta=meta)

        if next_page:
            meta = {'website': response.meta.get('website'), 'limit': limit}
            data = self.hz_data.copy()
            data["currpage"] = int(data.get("currpage")) + 1
            yield scrapy.FormRequest(next_page, callback=self.parse_hz, headers=HEADERS, meta=meta, formdata=data)

    def hz_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        item = ZhengceContentItem()

        item["index_no"] = response.xpath('//*[@id="xxgk_tab"]/tr[1]/td[2]/text()').extract_first()
        item["cate"] = '通知文件'
        item["pub_dept"] = response.xpath('//*[@id="xxgk_tab"]/tr[3]/td[2]/text()').extract_first()
        item["write_date"] = ''
        item["pub_date"] = response.xpath('//*[@id="xxgk_tab"]/tr[2]/td[4]/text()').extract_first()
        item["pub_no"] = ''

        content_xpath = '//div[@class="articlect"]'
        content = xpath_from_remove(response, 'string({})'.format(content_xpath))
        # content = response.xpath('string({})'.format(content_xpath)).extract_first().strip()
        html_content = get_html_content(response, content_xpath)
        title = response.xpath('string(//div[@class="title"])').extract_first().strip()
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
        # print(item)
        yield item