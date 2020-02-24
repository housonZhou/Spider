# -*- coding: utf-8 -*-
import hashlib
import re
from urllib.parse import urljoin

import redis
import scrapy
from article.items import ArticleItem, ZhengcekuItem, ZhengceContentItem
from article.util import get_cookie, obj_first, get_html_content, time_map
from article.settings import HEADERS

m = hashlib.md5()
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
conn = redis.StrictRedis(connection_pool=pool)


class WhHanSpider(scrapy.Spider):
    name = 'WuHanWjwSpider'
    # allowed_domains = ['hubei.gov.cn']

    def start_requests(self):
        urls = [
            ("http://wjw.wuhan.gov.cn/front/web/list3rd/no/806", "武汉市-卫健委-法律法规"),
            ("http://wjw.wuhan.gov.cn/front/web/list2nd/no/710", "武汉市-卫健委-公示公告", "2020-01-23"),
            ("http://wjw.wuhan.gov.cn/front/web/list3rd/no/803", "武汉市-卫健委-通知公告"),
            ("http://wjw.wuhan.gov.cn/front/web/list3rd/no/802", "武汉市-卫健委-疫情通报"),
            ("http://wjw.wuhan.gov.cn/front/web/list3rd/no/804", "武汉市-卫健委-防控动态"),
            ("http://wjw.wuhan.gov.cn/front/web/list3rd/no/805", "武汉市-卫健委-健康科普"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, name, *limit in urls:
            yield scrapy.Request(url, meta={"website": name, 'limit': limit}, callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = obj_first(response.meta.get('limit'))
        tag = website.split('-')[-1]

        page = PageControl(response)
        next_page = page.next_page()

        for item in response.xpath('//*[@id="docList"]//a'):
            link = item.xpath('./@href').extract_first()
            url = urljoin(response.url, link)
            if limit:
                time_ = item.xpath('./span[@class="time"]/text()').extract_first()
                if time_ < limit:
                    next_page = None
                    continue
            # if ('beijing.gov.cn' not in url) or ('video' in url) or ('pdf' in url):
            #     continue
            conn.hset("bf", tag + '-' + url, 1)
            meta = {'tag': tag, 'website': website}
            # print(meta, url)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)

        if next_page:
            meta = {'website': response.meta.get('website'), 'limit': limit}
            # print(next_page, meta)
            yield scrapy.FormRequest(next_page.get('url'), callback=self.parse, headers=HEADERS, meta=meta,
                                     formdata=next_page.get('data'))

    def parse_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        # if ('govfile' in response.url) or ('zfwj' in response.url):
        #     item = self.zhengceContent(response)
        # elif '' in response.url:
        #     item = self.zhengceku(response)
        # else:
        #     item = self.article(response)

        item = self.article(response)
        item["tag"] = response.meta.get('tag')
        item["website"] = response.meta.get('website')
        item["url"] = response.url
        item["article_id"] = article_id
        # print(item)
        yield item

    @staticmethod
    def zhengceContent(response):
        item = ZhengceContentItem()
        other_items = response.xpath('//div[@class="col-xs-12 metadata_content"]/div[@class="row"]/div')
        replace_dict = {
            'index_no': '索引号',
            'cate': '分类',
            'pub_dept': '发布机构',
            'write_date': '发文日期',
            'pub_date': '发布日期',
            'pub_no': '文号',
            'is_effective': '效力状态',
        }
        for other in other_items:
            doc = other.xpath('./strong/text()').extract_first()
            doc = re.sub(r'\s', '', doc)
            span = other.xpath('./text()').extract()[1]
            for k, v in replace_dict.items():
                if v in doc:
                    item[k] = span.strip()
        for k in replace_dict:
            if k not in item:
                item[k] = ''
        # item["index_no"] = index_no
        # item["cate"] = cate
        # item["pub_dept"] = pub_dept
        # item["write_date"] = write_date
        # item["pub_date"] = pub_date
        # item["pub_no"] = pub_no

        content = response.xpath('string(//div[@class="row content_block"])').extract_first().strip()
        title = response.xpath('string(//h2)').extract_first().strip()
        attach = response.xpath('//div[@class="row content_block"]//a')
        attachment = []
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = urljoin(response.url, url_)
            attachment.append((file_name, download_url))
        item["content"] = content
        item["title"] = title
        item["attachment"] = attachment
        return item

    """
    @staticmethod
    def zhengceku(response):
        item = ZhengcekuItem()
        item["source"] = source
        item["file_type"] = file_type
        item["cate"] = cate
        item["pub_dept"] = pub_dept
        item["write_date"] = write_date
        item["pub_date"] = pub_date
        item["content"] = content
        item["title"] = title
        item["pub_no"] = pub_no
        item["attachment"] = attachment
        item["is_effective"] = is_effective
        item["effective_start"] = effective_start
        item["effective_end"] = effective_end
        return item
    """

    @staticmethod
    def article(response):
        title = response.xpath('string(//h1)').extract_first()
        other = response.xpath('string(//h2)').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：\s*([^\s|]*)\s*', other))
        pub_dept = obj_first(re.findall(r'发布机构：\s*([^\s|]*)\s*', other))
        if not source and pub_dept:
            source = pub_dept
        # 正文识别区
        content_xpath = '//*[@id="detailContent"]'
        content = response.xpath('string({})'.format(content_xpath)).extract_first().strip()
        html_content = get_html_content(response, content_xpath)
        image_url = response.xpath('{}//img/@src'.format(content_xpath)).extract()
        image_url = [urljoin(response.url, i) for i in image_url]
        attach = response.xpath('{}//a'.format(content_xpath))
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
        return item

    def parse_test(self, response: scrapy.http.Response):
        content = response.xpath('//*[@id="detailContent"]').get()
        print(content)
        print('+++++')
        content = re.sub(r'<([a-z]+).*?>', r'<\1>', content)
        print(content)
        print('=====')
        print(response.xpath('string(//*[@id="detailContent"])').extract_first())


class PageControl:
    """
    <form id="pageForm" method="post" action="http://wjw.wuhan.gov.cn:80/front/web/list3rd/yes/805">
        <input type="hidden" id="pageNum" name="pageNum" value="2" /><!-- 当前页面 -->
        <input type="hidden" id="numPerPage" name="numPerPage" value="15" /><!-- 每页大小 -->
        <input type="hidden" name="orderField" value="publishDate" /><!-- 排序字段 -->
        <input type="hidden" name="orderDirection" value="DESC" /><!-- 排序升序还是降序 -->
        <input type="hidden" name="keywords" value=""/>
    </form>
    """
    def __init__(self, response):
        self.find = response.xpath('//*[@id="pageForm"]/input')
        self.base_url = response.xpath('//*[@id="pageForm"]/@action').extract_first()
        self.form_data = {}
        for item in self.find:
            name = item.xpath('./@name').extract_first()
            value = item.xpath('./@value').extract_first()
            self.form_data[name] = value
        msg = response.xpath('//div[@class="control"]/span/text()').extract_first()
        if msg:
            self.end, self.now = re.findall(r'(\d+)页', msg)
        else:
            self.end = self.now = None

    def next_page(self):
        if self.end == self.now:
            return None
        else:
            self.form_data["pageNum"] = str(int(self.form_data["pageNum"]) + 1)
        return {'url': self.base_url, 'data': self.form_data}
