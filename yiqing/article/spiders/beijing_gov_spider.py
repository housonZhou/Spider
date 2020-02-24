# -*- coding: utf-8 -*-
import hashlib
import re
from urllib.parse import urljoin

import redis
import scrapy
from article.items import ArticleItem, ZhengcekuItem, ZhengceContentItem
from article.util import return_tag, get_cookie
from article.settings import HEADERS

m = hashlib.md5()
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
conn = redis.StrictRedis(connection_pool=pool)


class YiqingSpider(scrapy.Spider):
    name = 'BeiJIngGovSpider'

    def start_requests(self):
        # # 国务院
        urls = [
            ("http://www.beijing.gov.cn/ywdt/zwzt/yqfk/zcwj/", "北京市-人民政府-政策文件及解读"),
            ("http://www.beijing.gov.cn/fuwu/lqfw/ztzl/zczxwqy/xlsd/", "北京市-人民政府-政策文件"),
            ("http://www.beijing.gov.cn/fuwu/lqfw/ztzl/zczxwqy/18/", "北京市-人民政府-文件解读"),
            ("http://www.beijing.gov.cn/ywdt/zwzt/yqfk/yqbb/", "北京市-人民政府-疫情通报"),
            ("http://www.beijing.gov.cn/ywdt/zwzt/yqfk/bjfk/", "北京市-人民政府-北京防控"),
            ("http://www.beijing.gov.cn/ywdt/zwzt/yqfk/gqxd/", "北京市-人民政府-各区行动"),
            ("http://www.beijing.gov.cn/ywdt/zwzt/yqfk/qwhy/", "北京市-人民政府-权威回应"),
            ("http://www.beijing.gov.cn/ywdt/zwzt/yqfk/kpzs/", "北京市-人民政府-防控指南"),
        ]
        # cookies = get_cookie('http://www.beijing.gov.cn/fuwu/lqfw/ztzl/zczxwqy/18/')
        for url, name in urls:
            yield scrapy.Request(url, meta={"website": name}, callback=self.parse, headers=HEADERS)

    def parse(self, response):
        website = response.meta["website"]
        # tag = response.xpath('//span[@class="tabg"]/text()').extract()[0].strip()
        tag = website.split('-')[-1]
        print("爬取 ", tag)
        articles = response.xpath('//ul/li[@class="col-md"]')
        current_page = response.xpath('//div[@class="changepage"]/script/text()').extract_first()
        current = int(re.findall(r'current\:(\d+)', current_page)[0])
        total = int(re.findall(r'size\:(\d+)', current_page)[0])
        prefix = re.findall(r'prefix\:\'(.*?)\'', current_page)[0]
        suffix = re.findall(r'suffix\:\'(.*?)\'', current_page)[0]
        print("当前爬取页：{}，总共{}页".format(current, total))

        for a_dom in articles:
            # title = a_dom.xpath("./a/text()").extract()[0]
            href = a_dom.xpath("./a/@href").extract_first()
            link = urljoin(response.url, href)
            # print(title, link, sep='\n')
            # 不采集视频文章
            # if "cntv" in href:
            #     print(title, href, "放弃原因：视频")
            #     continue
            # 判断是否采集完成
            # if conn.hget("bf", tag + '-' + href):
            #     print("采集完成，网站{}的{}板块({}) 最新数据为{}({})".format(website, tag, response.url, title, href))
            #     return
            # else:
            #     conn.hset("bf",  tag + '-' + href, 1)
            conn.hset("bf", tag + '-' + link, 1)

            # 浏览更多政策请点击进入“文件库”>>>
            # if " http://www.gov.cn/zhengce/xxgkzl.htm" == href:
            #     continue

            # 进入详情页
            if "zhengcefagui" in link:
                yield scrapy.Request(url=link, callback=self.parse_zhengce_zhengceku,
                                     meta={"tag": tag, "website": website}, headers=HEADERS)
            else:
                yield scrapy.Request(url=link, callback=self.parse_content,
                                     meta={"tag": tag, "website": website}, headers=HEADERS)
        if total - 1 > current:
            base_url = response.url.split('/')
            base_url[-1] = '{}_{}.{}'.format(prefix, current + 1, suffix)
            next_page_url = '/'.join(base_url)
            yield scrapy.Request(next_page_url, callback=self.parse, meta={"website": website}, headers=HEADERS)

    def parse_content(self, response):
        tag = response.meta["tag"]
        website = response.meta["website"]
        title = response.xpath('//div[@class="header"]//p/text()').extract_first().strip()
        url = response.url
        other_message = response.xpath('string(//p[@class="fl"])').extract_first()
        pub_time = re.findall(r'\d{4}\D\d{1,2}\D\d{1,2}', other_message)[0]
        source = re.findall(r'来源：(\S*)', other_message)[0]  # 来源：北京市卫生健康委员会

        content_str = '//*[@id="mainText"]'
        content = response.xpath('string({})'.format(content_str)).extract_first().strip()

        html_content = response.xpath(content_str).get()
        html_content = re.sub(r'<([a-z]+).*?>', r'<\1>', html_content)

        images = response.xpath('{}//img/@src'.format(content_str)).extract()
        # base_url = "http://" + "/".join(url.split('/')[2:-1]) + "/"
        images = [urljoin(url, image) for image in images]
        article_id = hashlib.md5(url.encode()).hexdigest()

        article = ArticleItem()
        article["article_id"] = article_id
        article["tag"] = tag
        article["website"] = website
        article["title"] = title
        article["url"] = url
        article["pub_time"] = pub_time
        article["source"] = source
        article["content"] = content
        article["image_url"] = images
        article["html_content"] = html_content
        # print(article)
        yield article

    def parse_zhengce_zhengceku(self, response):
        tag = response.meta["tag"]
        website = response.meta["website"]
        url = response.url
        article_id = hashlib.md5(url.encode()).hexdigest()

        # 标题
        title = response.xpath('//div[@class="header"]//p/text()').extract_first().strip()

        tables = response.xpath('//ol/li')
        # print(response.body.decode())
        for item in tables:
            doc = item.xpath('./text()').extract_first()
            span = item.xpath('./span/text()').extract_first()
            span = span if span else ''
            if '发文机构' in doc:
                pub_dept = span
            elif '联合发文单位' in doc:
                pub_other = span
            elif '发文字号' in doc:
                pub_no = span
            elif '主题分类' in doc:
                cate = span
            elif '成文日期' in doc:
                write_date = span
            elif '发布日期' in doc:
                pub_date = span
            elif '有效性' in doc:
                is_effective = span
            elif '实施日期' in doc:
                effective_start = span
            elif '废止日期' in doc:
                effective_end = span
        if pub_other:
            pub_dept = '{};{}'.format(pub_dept, pub_other)

        # 公文种类
        file_type = ''.join(
            response.xpath('//div[@class="policyLibraryOverview_header"]//tr[4]/td[4]/text()').extract())

        content_str = '//*[@id="mainText"]'
        content = response.xpath('string({})'.format(content_str)).extract_first().strip()

        html_content = response.xpath(content_str).get()
        html_content = re.sub(r'<([a-z]+).*?>', r'<\1>', html_content)
        # 附件信息
        attach = response.xpath('//ul[@class="fujian"]/li/a')
        attachment = []
        for a in attach:
            file_name = a.xpath('./text()').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = urljoin(url, url_)
            attachment.append((file_name, download_url))

        item = ZhengcekuItem()
        item["source"] = ''
        item["file_type"] = file_type
        item["cate"] = cate
        item["pub_dept"] = pub_dept
        item["write_date"] = write_date
        item["pub_date"] = pub_date
        item["content"] = content
        item["title"] = title
        item["pub_no"] = pub_no
        item["tag"] = tag
        item["website"] = website
        item["url"] = url
        item["article_id"] = article_id
        item["attachment"] = attachment
        item["is_effective"] = is_effective
        item["effective_start"] = effective_start
        item["effective_end"] = effective_end
        item["html_content"] = html_content
        print(item)
        yield item

    def parse_zhengce_content(self, response):
        tag = response.meta["tag"]
        website = response.meta["website"]
        url = response.url
        article_id = hashlib.md5(url.encode()).hexdigest()

        # 索引号
        index_no = ''.join(response.xpath('//td/table[@class="bd1"][1]//tr[1]/td[2]/text()').extract())
        # 主题分类
        cate = ''.join(response.xpath('//td/table[@class="bd1"][1]//tr[1]/td[4]/text()').extract()).replace('\\', '/')
        # 发文机关
        pub_dept = ''.join(response.xpath('//td/table[@class="bd1"][1]//tr[2]/td[2]/text()').extract())
        # 成文日期
        write_date = ''.join(response.xpath('//td/table[@class="bd1"][1]//tr[2]/td[4]/text()').extract())
        # 标题
        title = ''.join(response.xpath('//td/table[@class="bd1"][1]//tr[3]/td[2]/text()').extract())
        # 发文字号
        pub_no = ''.join(response.xpath('//td/table[@class="bd1"][1]//tr[4]/td[2]/text()').extract())
        # 发文日期
        pub_date = ''.join(response.xpath('//td/table[@class="bd1"][1]//tr[2]/td[4]/text()').extract())
        # 正文
        content = ''.join(response.xpath('//td[@id="UCAP-CONTENT"]//text()').extract()).replace('"', '\"')


        item = ZhengceContentItem()
        item["index_no"] = index_no
        item["cate"] = cate
        item["pub_dept"] = pub_dept
        item["write_date"] = write_date
        item["pub_date"] = pub_date
        item["content"] = content
        item["title"] = title
        item["pub_no"] = pub_no
        item["tag"] = return_tag(title, tag, "")
        item["website"] = website
        item["url"] = url
        item["article_id"] = article_id

        yield item
