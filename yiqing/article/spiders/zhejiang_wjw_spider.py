# -*- coding: utf-8 -*-
import hashlib
import re
from urllib.parse import urljoin

import redis
import json
import scrapy
from article.items import ArticleItem, ZhengcekuItem, ZhengceContentItem
from article.util import get_cookie, obj_first, get_html_content, time_map, query2dict, parse2query
from article.settings import HEADERS

m = hashlib.md5()
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
conn = redis.StrictRedis(connection_pool=pool)


class ZheJiangWjwSpider(scrapy.Spider):
    name = 'ZheJiangWjwSpider'
    # allowed_domains = ['hubei.gov.cn']

    def start_requests(self):
        urls = [
            # ("http://www.blueskyinfo.com.cn/wjwApp/data/genInfoData.do?topicId=001001&currentPage=0&perPage=100", "浙江省-卫健委-信息发布"),
            # ("http://www.blueskyinfo.com.cn/wjwApp/data/genInfoData.do?topicId=001002&currentPage=0&perPage=100", "浙江省-卫健委-宣传教育"),
        ]
        # self.cookies = get_cookie('http://www.nhc.gov.cn/xcs/yqtb/202002/ac1e98495cb04d36b0d0a4e1e7fab545.shtml')
        for url, name, *limit in urls:
            limit = obj_first(limit)
            yield scrapy.Request(url, meta={"website": name, 'limit': limit}, callback=self.parse, headers=HEADERS)
        post_data = {
            "col": "1",
            "appid": "1",
            "webid": "1855",
            "path": "/",
            "columnid": "1202101",
            "sourceContentType": "1",
            "unitid": "4978845",
            "webname": "浙江省卫生健康委员会",
            "permissiontype": "0"
        }
        post_urls = [
            ("http://www.zjwjw.gov.cn/module/jpage/dataproxy.jsp?startrecord=1&endrecord=42&perpage=14",
             "浙江省-卫健委-通知公告",
             "1202101",
             "2020-01-23"),
            ("http://www.zjwjw.gov.cn/module/jpage/dataproxy.jsp?startrecord=1&endrecord=42&perpage=14",
             "浙江省-卫健委-工作动态",
             "1663145"),
        ]
        self.post_headers = {
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "www.zjwjw.gov.cn",
            "Origin": "http://www.zjwjw.gov.cn",
            "Referer": "http://www.zjwjw.gov.cn/col/col1202101/index.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Cookie": "JSESSIONID=9CE6F2222FC99DF31D6E92DD55889BA9; acw_tc=784e2c9115822711277594622e4615cb97eed8322636b2bf933277ccc613fc; SERVERID=d2e5436f826f0ca88944db105fd8663e|1582347627|1582347520"
        }
        for url, name, columnid, *limit in post_urls:
            limit = obj_first(limit)
            form_data = post_data.copy()
            form_data["columnid"] = columnid
            print(form_data)
            yield scrapy.FormRequest(url, meta={"website": name, 'limit': limit, 'data': form_data.copy()}, callback=self.parse_post,
                                     formdata=form_data, method='POST', headers=self.post_headers)

    def parse_post(self, response: scrapy.http.Response):
        resp = response.text
        url = response.url
        tag = response.meta.get('website').split('-')[-1]
        limit = response.meta.get('limit')
        total = obj_first(re.findall(r'<totalrecord>(\d+)</totalrecord>', resp))
        next_parse = query2dict(url)
        start = int(next_parse.get('startrecord'))
        end = int(next_parse.get('endrecord'))
        if end + 1 < int(total):
            next_page = parse2query(parse_data={'startrecord': start + 42, 'endrecord': end + 42, 'perpage': 14},
                                    url_replace=url)
        else:
            next_page = None
        for href, other_time in re.findall(r"<li><a href='(.*?)'.*?<span>(.*?)</span></li>", resp):
            other_time = time_map(other_time)
            detail_url = urljoin(url, href)
            if limit:
                if other_time < limit:
                    next_page = None
                    continue
            if 'zjwjw.gov.cn' not in detail_url:
                continue
            conn.hset("bf", tag + '-' + url, 1)
            yield scrapy.Request(detail_url, callback=self.post_detail,
                                 headers=HEADERS, meta={'website': response.meta.get('website')})
        if next_page:
            data = response.meta.get('data')
            website = response.meta.get('website')
            yield scrapy.FormRequest(next_page,
                                     meta={"website": website, 'limit': limit, 'data': data.copy()},
                                     callback=self.parse_post, formdata=data.copy(),
                                     method='POST', headers=self.post_headers)

    def post_detail(self, response: scrapy.http.Response):
        article_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.xpath('string(//div[@class="wz"]/p)').extract_first().strip()
        other = response.xpath('string(//div[@class="fbrq clearfix"])').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：\s*(\S*)', other))
        # 正文识别区
        content_xpath = '//*[@id="zoom"]'
        content = response.xpath('string({})'.format(content_xpath)).extract_first().strip()
        html_content = get_html_content(response, content_xpath)
        image_url = response.xpath('{}//img/@src'.format(content_xpath)).extract()
        image_url = [urljoin(response.url, i) for i in image_url]
        attach = response.xpath('{}//a[not(@href="javascript:")]'.format(content_xpath))
        attachment = []
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = urljoin(response.url, url_)
            if file_name:
                attachment.append((file_name, download_url))

        item = ArticleItem()
        item["title"] = title
        item["pub_time"] = pub_time
        item["source"] = source
        item["content"] = content
        item["image_url"] = image_url
        item["attachment"] = attachment
        item["html_content"] = html_content
        website = response.meta.get('website')
        item["tag"] = website.split('-')[-1]
        item["website"] = website
        item["url"] = response.url
        item["article_id"] = article_id
        # print(item)
        yield item

    def parse(self, response: scrapy.http.Response):
        website = response.meta.get('website')
        limit = response.meta.get('limit')
        tag = website.split('-')[-1]
        response_json = json.loads(response.text)
        data = response_json.get('data', '[];')
        if data != '[];':
            page = int(re.findall(r'currentPage=(\d+)', response.url)[0])
            next_page = response.url.replace('currentPage={}'.format(page),
                                             'currentPage={}'.format(page + 1))
        else:
            next_page = None
        for uid, other_time in re.findall(r'"I\$(\w+?)\$.*?\$(\d{4}\D\d{1,2}\D\d{1,2})"', data):
            url = 'http://www.blueskyinfo.com.cn/wjwApp/webinfo/infoDetail.do?infoIds={}'.format(uid)
            if limit:
                if other_time < limit:
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
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

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
        title = response.xpath('string(//h2)').extract_first()
        other = response.xpath('string(//h4)').extract_first()
        pub_time = time_map(other)
        source = obj_first(re.findall(r'来源：(\S*)', other))
        # 正文识别区
        content_xpath = '//td[@class="text-left"]'
        content = response.xpath('string({})'.format(content_xpath)).extract_first().strip()
        html_content = get_html_content(response, content_xpath)
        image_url = response.xpath('{}//img/@src'.format(content_xpath)).extract()
        image_url = [urljoin(response.url, i) for i in image_url]
        attach = response.xpath('{}//a[not(@href="javascript:")]'.format(content_xpath))
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
        from lxml.etree import HTML
        content = HTML(response.text)
        for dom in content.xpath('//script'):
            new_content = dom.getparent()
            new_content.remove(dom)
        print(content.xpath('string(//*[@id="xw_box"])'))
