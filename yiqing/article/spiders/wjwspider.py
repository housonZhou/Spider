# -*- coding: utf-8 -*-
import hashlib
import re

import redis
import scrapy
from article.items import ArticleItem, PressItem
from article.util import return_tag

m = hashlib.md5()
pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
conn = redis.StrictRedis(connection_pool=pool)


class YiqingSpider(scrapy.Spider):
    name = 'wjwspider'

    def start_requests(self):
        # 测试
        # wjw_cookie = get_cookie("http://www.nhc.gov.cn/xcs/kpzs/list_gzbd_5.shtml")
        # url= 'http://www.nhc.gov.cn/xwzb/webcontroller.do?titleSeq=11224&gecstype=1'
        # yield scrapy.Request(url, meta={"website": "test_website", "tag": "test_tag"},
        #                      callback=self.parse_public_detail)  # , cookies=wjw_cookie)

        # 卫生健康委员会
        urls = [
            # ("http://www.nhc.gov.cn/xcs/yqtb/list_gzbd.shtml", "卫健委-防控动态-疫情通报"),
            # ("http://www.nhc.gov.cn/xcs/fkdt/list_gzbd.shtml", "卫健委-防控动态-防控动态"),
            # ("http://www.nhc.gov.cn/xcs/kpzs/list_gzbd.shtml", "卫健委-防控动态-防控知识"), #没爬

            # ("http://www.nhc.gov.cn/xcs/xwbd/list_gzbd.shtml", "卫健委-新闻报导-新闻报导"),
            # ("http://www.nhc.gov.cn/xcs/yhfc/list_gzbd.shtml", "卫健委-新闻报导-防疫宣传"),
            ("http://www.nhc.gov.cn/xcs/zhengcwj/list_gzbd.shtml", "卫健委-政策文件-通知公告"),
        ]
        for url, name in urls:
            yield scrapy.Request(url, meta={"website": name}, callback=self.parse_wjw)

        # urls = [
        #     ("http://www.nhc.gov.cn/xwzb/ShowAllServlet?typeSeq=1&page=1", "卫健委-新闻报导-新闻发布会"),
        # ]
        # for url, name in urls:
        #     yield scrapy.Request(url, meta={"website": name}, callback=self.parse_public_list)

    def parse_wjw(self, response):
        website = response.meta["website"]
        tag = response.xpath('//div[@class="index_title"]/h3/text()').extract()[0].strip()
        print("爬取 ", tag)
        articles = response.xpath('//ul[@class="zxxx_list"]//a')
        # current_page = response.xpath('//div[@class="pagination_index_last"]/text()[1]').extract()[0]
        max_page, current_page = re.findall(r"'page_div',(\d+), (\d+),'", response.text)[0]  # 1, 1
        print("当前爬取页：", current_page)

        # 详情页url拼接规则
        base_url = '/'.join(response.url.split('/')[:3])
        for a_dom in articles:
            href = base_url + a_dom.xpath('./@href').extract()[0]
            title = a_dom.xpath('./text()').extract()[0]
            if "[视频]" in title:
                print(title, href, "放弃原因：视频")
                continue
            # 判断是否采集完成
            # if conn.hget("bf", tag + '-' + href):
            #     print("采集完成，网站{}的{}板块({}) 最新数据为{}({})".format(website, tag, response.url, title, href))
            #     return
            # else:
            #     conn.hset("bf", tag + '-' + href, 1)
            print(title, href)

            # 进入详情页
            yield scrapy.Request(href, callback=self.parse_wjw_detail, meta={"tag": tag, "website": website})

        # 下一页
        if int(max_page) > int(current_page):
            try:
                next_page_url = re.sub(r'(_\d+)?\.shtml', "_%s.shtml" % (int(current_page) + 1), response.url)
            except:
                print(website, tag, "已到达末页")
            else:
                print("next_page_url", next_page_url)
                # 翻页
                yield scrapy.Request(next_page_url, callback=self.parse_wjw, meta={"website": website})

    def parse_wjw_detail(self, response):
        tag = response.meta["tag"]
        website = response.meta["website"]
        url = response.url
        article_id = hashlib.md5(url.encode()).hexdigest()
        title = ''.join(response.xpath('//div[@class="tit"]/text()').extract()).replace('"', '\\"')
        pub_time = ''.join(response.xpath('//div[@class="source"]//text()[contains(.,"发布时间")]').extract()).split()[-1]
        source = ''.join(response.xpath('//div[@class="source"]//text()[contains(.,"来源")]').extract()).split()
        if len(source) == 1:
            source = ''
        else:
            source = source[-1]
        content = ''.join(response.xpath('//div[@id="xw_box"]/p/text()').extract()).replace('"', '\\"')
        images = response.xpath('//div[@id="xw_box"]/p/img/@src').extract()
        base_url = "http://" + "/".join(url.split('/')[2:-1]) + "/"
        images = [base_url + image for image in images]

        # print(tag)
        # print(website)
        # print(article_id)
        print(title)
        print(url)
        # print(pub_time)
        # print(source)
        # print(content)

        article = ArticleItem()
        article["article_id"] = article_id
        article["tag"] = tag  # return_tag(title, tag, source)
        article["website"] = website
        article["title"] = title
        article["url"] = url
        article["pub_time"] = pub_time
        article["source"] = source
        article["content"] = content
        article["image_url"] = images
        yield article

    def parse_public_list(self, response):
        # print(response.text)
        website = response.meta['website']
        tag = "新闻发布会"
        presses = response.xpath('//table//table')
        base_url = 'http://www.nhc.gov.cn'

        navigator_params = response.xpath('//body/@onload').extract()[
            0]  # createPageHTML('showpage','31','30','ShowAllServlet?typeSeq=1');
        max_page, current_page = re.findall(r"'showpage','(\d+)','(\d+)'", navigator_params)[0]
        print("当前爬取页：", current_page)

        for press in presses:
            href = press.xpath('.//a[contains(./text(),"直播实录")]/@href').extract()[0]
            title = ''.join(press.xpath('.//tr[1]/td[1]//text()').extract())
            # 判断是否采集完成
            # if conn.hget("bf", tag + '-' + base_url + href):
            #     print("采集完成，网站{}的{}板块({}) 最新数据为{}({})".format(website, tag, response.url, title, base_url + href))
            #     return
            # else:
            #     conn.hset("bf", tag + '-' + base_url + href, 1)
            print(title, base_url + href)

            yield scrapy.Request(base_url + href, meta={'website': website, 'tag': tag},
                                 callback=self.parse_public_detail)

        # 下一页
        if int(max_page) > int(current_page):
            next_page_url = "http://www.nhc.gov.cn/xwzb/ShowAllServlet?typeSeq=1&page=" + str(int(current_page) + 1)
            print("next_page_url:", next_page_url)
            yield scrapy.Request(next_page_url, meta={"website": website}, callback=self.parse_public_list)

    def parse_public_detail(self, response):
        tag = response.meta["tag"]
        website = response.meta["website"]
        url = response.url
        article_id = hashlib.md5(url.encode()).hexdigest()
        title = ''.join(response.xpath('//span[@class="STYLE2"]//text()').extract()).replace('"', '\\"').strip()
        pub_time = ''.join(response.xpath('//tr[contains(./td/text(), "时间")]/td[2]/text()').extract())
        state = ''.join(response.xpath('//tr[contains(./td/text(), "状态")]/td[2]//text()').extract()).strip()
        location = ''.join(response.xpath('//tr[contains(./td/text(), "地点")]/td[2]//text()').extract())
        guest = '\r\n'.join(response.xpath('//tr[contains(./td/text(), "嘉宾")]/td[2]//text()').extract())
        abstract = ''.join(response.xpath('//tr[contains(./td/text(), "内容")]/td[2]//text()').extract())

        images = response.xpath('//img/@src').extract()
        base_url = 'http://www.nhc.gov.cn'
        images = [base_url + image for image in images]

        # print(tag)
        # print(website)
        # print(article_id)
        # print(title)
        # print(url)
        # print(pub_time)
        # print(source)
        # print(content)
        # print(images)

        press = PressItem()
        press["article_id"] = article_id
        press["website"] = website
        press["tag"] = tag
        press["state"] = state
        press["location"] = location
        press["guest"] = guest
        press["abstract"] = abstract
        press["title"] = title
        press["url"] = url
        press["pub_time"] = pub_time
        press["image_url"] = images
        msglist = response.xpath('//iframe[@id="gg"]/@src[1]').extract()[0]
        yield scrapy.Request("http://www.nhc.gov.cn/" + msglist, meta={"item": press}, callback=self.parse_msglist)

    def parse_msglist(self, response):
        press = response.meta['item']
        content = ''.join(response.xpath('//td[@class="hei14"]//text()').extract()).replace('\t', '').replace('\r',
                                                                                                              '').replace(
            '\n', '').replace(' ', '').replace('"', '\\"')
        press['content'] = content
        yield press
