# -*- coding: utf-8 -*-
import hashlib
import re
from urllib.parse import urljoin

import redis
import scrapy
from article.items import ArticleItem, ZhengcekuItem, ZhengceContentItem
from article.util import get_cookie, time_map, obj_first, get_html_content
from article.settings import HEADERS

m = hashlib.md5()
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
conn = redis.StrictRedis(connection_pool=pool)


class HuBeiSpider(scrapy.Spider):
    name = 'HuBeiGovSpider'
    # allowed_domains = ['hubei.gov.cn']

    def start_requests(self):

        urls = [
            ("http://www.hubei.gov.cn/xxgk/gsgg/", "湖北省-人民政府-公示公告"),
            ("http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/zxtb/", "湖北省-人民政府-权威通报"),
            ("http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/qfqk/", "湖北省-人民政府-联防联控"),
            ("http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/ys/", "湖北省-人民政府-英雄群谱"),
            ("http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/kp/", "湖北省-人民政府-战疫快评"),  #
            ("http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/fkkp/", "湖北省-人民政府-防控科普"),  #
            ("http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/py/", "湖北省-人民政府-科学辟谣"),  #
        ]
        self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, name in urls:
            yield scrapy.Request(url, meta={"website": name}, callback=self.parse,
                                 headers=HEADERS, cookies=self.cookies)

    def parse(self, response: scrapy.http.Response):
        # Cookie = response.request.headers.getlist('Cookie')
        # SetCookie = response.headers.getlist('Set-Cookie')
        # print('Cookie:', Cookie)
        # print('SetCookie: ', SetCookie)
        tag = response.xpath('//ol[@class="breadcrumb"]/li[@class="active"]/a/text()').extract_first()
        for link in response.xpath('//ul[@class="list-unstyled news_list"]/li/a/@href').extract():
            url = urljoin(response.url, link)
            if 'hubei.gov.cn' not in url:
                continue
            conn.hset("bf", tag + '-' + url, 1)
            meta = {'tag': tag, 'website': response.meta.get('website')}
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, cookies=self.cookies, meta=meta)
        page = PageControl(response.text)
        next_page = page.next_page(response.url)
        if next_page:
            meta = {'website': response.meta.get('website')}
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, cookies=self.cookies, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        if ('govfile' in response.url) or ('zfwj' in response.url):
            item = self.zhengceContent(response)
        # elif '' in response.url:
        #     item = self.zhengceku(response)
        else:
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
        html_content = get_html_content(response, '//div[@class="row content_block"]')
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
        item["html_content"] = html_content
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
        title = response.xpath('//h2/text()').extract_first()
        other = response.xpath('string(//div[@class="row metadata_block"]//ul[@class="list-unstyled list-inline"])').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：(\S*)', other))
        content = response.xpath('string(//div[@class="row content_block"])').extract_first().strip()
        html_content = get_html_content(response, '//div[@class="row content_block"]')
        image_url = response.xpath('//div[@class="row content_block"]//img/@src').extract()
        image_url = [urljoin(response.url, i) for i in image_url]
        attach = response.xpath('//div[@class="row content_block"]//a')
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


class PageControl:
    """
    翻页器： pageControl(4, 2, "index", "shtml", 10, 'pages-nav');
             http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/zy/index_2.shtml
    """
    def __init__(self, response):
        self.find = re.findall(r'pageControl(.*?);', response)
        try:
            self.total, self.now, self.default, self.type, *_ = eval(self.find[0])
        except:
            self.total = self.now = self.default = self.type = None

    def next_page(self, url):
        if not self.find:
            return None
        elif self.total - 1 > self.now:
            base_url = url.split('/')
            base_url[-1] = '{}_{}.{}'.format(self.default, self.now + 1, self.type)
            return '/'.join(base_url)
        else:
            return None
