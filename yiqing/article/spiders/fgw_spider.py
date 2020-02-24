# -*- coding: utf-8 -*-
import hashlib
import re
from urllib.parse import urljoin

import redis
import scrapy
from article.items import ArticleItem, ZhengcekuItem, ZhengceContentItem
from article.util import get_cookie, obj_first, get_html_content, time_map, xpath_from_remove
from article.settings import HEADERS
from lxml.etree import HTML

m = hashlib.md5()
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
conn = redis.StrictRedis(connection_pool=pool)


class FGWSpider(scrapy.Spider):
    name = 'FGWSpider'
    # allowed_domains = ['hubei.gov.cn']

    def start_requests(self):
        self.cookies_hb = get_cookie('http://fgw.hubei.gov.cn/fbjd/tzgg/tz/')
        print(self.cookies_hb)
        urls = [
            ("发改委-发改委-通知", "https://www.ndrc.gov.cn/xxgk/zcfb/tz/", self.parse_fgw, {}, '2020-01-23'),
            ("深圳市-发改委-通知公告", "http://fgw.sz.gov.cn/zwgk/qt/tzgg/", self.parse_sz, {}, '2020-01-23'),
            ("广东省-发改委-业务通知", "http://drc.gd.gov.cn/ywtz/index.html", self.parse_gd, {}, '2020-01-23'),
            ("上海市-发改委-最新信息公开", "http://fgw.sh.gov.cn/info/iList.jsp?cat_id=10199&cur_page=1"), #
            ("广州市-发改委-通知公告", "http://fgw.gz.gov.cn/tzgg/index.html", self.parse_gz, {}, '2020-01-23'),
            ("湖北省-发改委-通知", "http://fgw.hubei.gov.cn/fbjd/tzgg/tz/", self.parse_hb, self.cookies_hb, '2020-01-23'),
        ]
        for name, url, call, cookies, *limit in urls:
            yield scrapy.Request(url, meta={"website": name, 'limit': limit},
                                 callback=call, headers=HEADERS, cookies=cookies)

        # "上海市-发改委-最新信息公开" 一次性，不用更新
        # url_sh = [
        #     "http://fgw.sh.gov.cn/xxgk/cxxxgk/37629.htm",
        #     "http://fgw.sh.gov.cn/xxgk/cxxxgk/37659.htm",
        #     "http://fgw.sh.gov.cn/xxgk/cxxxgk/37665.htm",
        #     "http://fgw.sh.gov.cn/xxgk/cxxxgk/37711.htm",
        #     "http://fgw.sh.gov.cn/xxgk/cxxxgk/37712.htm",
        #     "http://fgw.sh.gov.cn/xxgk/cxxxgk/37720.htm",
        #     "http://fgw.sh.gov.cn/xxgk/cxxxgk/37724.htm"
        # ]
        # for url in url_sh:
        #     conn.hset("bf", '最新信息公开' + '-' + url, 1)
        #     yield scrapy.Request(url, callback=self.sh_detail, headers=HEADERS,
        #                          meta={'tag': '最新信息公开', 'website': '上海市-发改委-最新信息公开'})

    def parse_fgw(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = obj_first(response.meta.get('limit'))
        tag = website.split('-')[-1]

        # page = PageControl(response)
        # next_page = page.next_page()

        for item in response.xpath('//ul[@class="u-list"]/li'):
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
            yield scrapy.Request(url, callback=self.fgw_detail, headers=HEADERS, meta=meta)

        # if next_page:
        #     meta = {'website': response.meta.get('website'), 'limit': limit}
            # print(next_page, meta)
            # yield scrapy.FormRequest(next_page.get('url'), callback=self.parse, headers=HEADERS, meta=meta,
            #                          formdata=next_page.get('data'))

    def fgw_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first()
        pub_no = obj_first(re.findall(r'\((.*?)\)', title))
        pub_date = time_map(response.xpath('//meta[@name="PubDate"]/@content').extract_first())
        source = response.xpath('//meta[@name="ContentSource"]/@content').extract_first()

        content_xpath = '//div[@class="TRS_Editor"]'
        content = response.xpath('string({})'.format(content_xpath)).extract_first().strip()
        html_content = get_html_content(response, content_xpath)
        attach = response.xpath('//div[@class="attachment"]//a'.format(content_xpath))
        attachment = []
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = urljoin(response.url, url_)
            attachment.append((file_name, download_url))
        other = ''.join(response.xpath('//div[@align="center"]//text()').extract())
        write_date = time_map(other)
        item = ZhengcekuItem()
        item["source"] = source
        item["file_type"] = ''
        item["cate"] = ''
        item["pub_dept"] = '中华人民共和国国家发展和改革委员会'
        item["write_date"] = write_date
        item["pub_date"] = pub_date
        item["content"] = content
        item["title"] = title
        item["pub_no"] = pub_no
        item["attachment"] = attachment
        item["is_effective"] = ''
        item["effective_start"] = ''
        item["effective_end"] = ''
        item["tag"] = response.meta.get('tag')
        item["website"] = response.meta.get('website')
        item["url"] = response.url
        item["article_id"] = article_id
        item["html_content"] = html_content
        # print(item)
        yield item

    def parse_sz(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = obj_first(response.meta.get('limit'))
        tag = website.split('-')[-1]
        # page = PageControl(response)
        # next_page = page.next_page()

        for item in response.xpath('//div[@class="con"]/ul/li/a'):
            link = item.xpath('./@href').extract_first()
            url = urljoin(response.url, link)
            if limit:
                time_ = time_map(item.xpath('./span[@class="p_sj"]/text()').extract_first())
                if time_ < limit:
                    next_page = None
                    continue
            # if ('beijing.gov.cn' not in url) or ('video' in url) or ('pdf' in url):
            #     continue
            conn.hset("bf", tag + '-' + url, 1)
            meta = {'tag': tag, 'website': website}
            # print(meta, url)
            yield scrapy.Request(url, callback=self.sz_detail, headers=HEADERS, meta=meta, encoding='gb2312')

        # if next_page:
        #     meta = {'website': response.meta.get('website'), 'limit': limit}
            # print(next_page, meta)
            # yield scrapy.FormRequest(next_page.get('url'), callback=self.parse, headers=HEADERS, meta=meta,
            #                          formdata=next_page.get('data'))

    def sz_detail(self, response: scrapy.http.Response):
        # 暂时放弃
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        text = response.body.decode('gbk')
        new_response = HTML(text)
        title = new_response.xpath('//meta[@name="ArticleTitle"]/@content')[0]
        other = new_response.xpath('string(//div[@class="h1_small"])')
        pub_time = time_map(other)
        source = '深圳市发展和改革委员会'

        # 正文识别区
        content_xpath = '//div[@class="TRS_Editor"]'
        content = new_response.xpath('string({})'.format(content_xpath)).strip()
        html_content = re.findall(r'(<div class=TRS_Editor>[\s\S]+?)<div class="Attachment"', text)[0].strip()
        image_url = response.xpath('{}//img/@src'.format(content_xpath)).extract()
        image_url = [urljoin(response.url, i) for i in image_url]
        attach = new_response.xpath('//div[@class="Attachment"]//a'.format(content_xpath))
        attachment = []
        for a in attach:
            file_name = a.xpath('string(.)')
            url_ = a.xpath('./@href')[0]
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
        item["html_content"] = html_content
        # print(item)
        yield item

    def parse_gd(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = obj_first(response.meta.get('limit'))
        tag = website.split('-')[-1]

        # page = PageControl(response)
        # next_page = page.next_page()

        for item in response.xpath('//ul[@class="comlist1 mt10 "]/li'):
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
            yield scrapy.Request(url, callback=self.gd_detail, headers=HEADERS, meta=meta)

        # if next_page:
        #     meta = {'website': response.meta.get('website'), 'limit': limit}
        # print(next_page, meta)
        # yield scrapy.FormRequest(next_page.get('url'), callback=self.parse, headers=HEADERS, meta=meta,
        #                          formdata=next_page.get('data'))

    def gd_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//h4)').extract_first().strip()
        other = response.xpath('string(//div[@class="jbxx clearfix"])').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：\s*(\S*)', other))
        # pub_dept = obj_first(re.findall(r'发布机构：\s*([^\s|]*)\s*', other))
        # if not source and pub_dept:
        #     source = pub_dept
        # 正文识别区
        content_xpath = '//*[@id="content1"]'
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

    def parse_gz(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = obj_first(response.meta.get('limit'))
        tag = website.split('-')[-1]

        # page = PageControl(response)
        # next_page = page.next_page()

        for item in response.xpath('//div[@class="list_li"]/ul/li'):
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

        # if next_page:
        #     meta = {'website': response.meta.get('website'), 'limit': limit}
        # print(next_page, meta)
        # yield scrapy.FormRequest(next_page.get('url'), callback=self.parse, headers=HEADERS, meta=meta,
        #                          formdata=next_page.get('data'))

    def gz_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//*[@id="zoomtitl"])').extract_first().strip()
        other = response.xpath('string(//*[@id="zoomtime"])').extract_first()
        pub_time = time_map(other)
        source = '广州市发展和改革委员会'
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

    def parse_hb(self, response: scrapy.http.Response):
        headers = response.request.headers
        website = response.meta.get('website')
        limit = obj_first(response.meta.get('limit'))
        tag = website.split('-')[-1]

        # page = PageControl(response)
        # next_page = page.next_page()
        for item in response.xpath('//div[@class="lsj-list"]/ul/li'):
            link = item.xpath('./a/@href').extract_first()
            url = urljoin(response.url, link)
            if limit:
                time_ = time_map(item.xpath('./a/i/text()').extract_first())
                if time_ < limit:
                    next_page = None
                    continue
            # if ('beijing.gov.cn' not in url) or ('video' in url) or ('pdf' in url):
            #     continue
            conn.hset("bf", tag + '-' + url, 1)
            meta = {'tag': tag, 'website': website}
            # print(meta, url)
            yield scrapy.Request(url, callback=self.hb_detail, headers=headers, meta=meta)

        # if next_page:
        #     meta = {'website': response.meta.get('website'), 'limit': limit}
        # print(next_page, meta)
        # yield scrapy.FormRequest(next_page.get('url'), callback=self.parse, headers=HEADERS, meta=meta,
        #                          formdata=next_page.get('data'))

    def hb_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//h2)').extract_first().strip()
        other = response.xpath('string(//div[@class="info"])').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：\s*(\S*)', other))
        # pub_dept = obj_first(re.findall(r'发布机构：\s*([^\s|]*)\s*', other))
        # if not source and pub_dept:
        #     source = pub_dept
        # 正文识别区
        content_xpath = '//*[@id="zwnr"]'
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

    def sh_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//h3)').extract_first().strip()
        other = response.xpath('string(//div[@class="xwzx_time1"])').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'发布机关：\s*(\S*)', other))
        pub_on = obj_first(re.findall(r'文\s*号：\s*(\S*)', other))
        # 正文识别区
        content_xpath = '//*[@id="xwzx_content_ds"]'
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
        if pub_on:
            item = ZhengcekuItem()
            item["pub_no"] = pub_on
            item["pub_dept"] = source
            item["cate"] = ''
            item["pub_date"] = pub_time
        else:
            item = ArticleItem()
            item["image_url"] = image_url
            item["pub_time"] = pub_time
        item["title"] = title
        item["source"] = source
        item["content"] = content
        item["attachment"] = attachment
        item["html_content"] = html_content
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
