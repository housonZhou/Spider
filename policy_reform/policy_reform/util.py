#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/2/7 5:31 下午
# @Author  : Anson
# @Contact : 1047053860@qq.com
# @Software: PyCharm
# @content :
import datetime
import re
import time
import redis
from urllib.parse import urlparse, urlencode, parse_qs

import scrapy
from lxml.etree import HTML
from selenium import webdriver
from selenium.webdriver import ChromeOptions

option = ChromeOptions()
option.add_experimental_option('excludeSwitches', ['enable-automation'])


def get_cookie(url):
    driver = webdriver.Chrome(options=option)
    driver.get(url)
    time.sleep(3)
    cookies = driver.get_cookies()
    driver.quit()
    items = []
    dict_ = {}
    for i in range(len(cookies)):
        cookie_value = cookies[i]
        item = cookie_value['name'] + '=' + cookie_value['value']
        items.append(item)
        dict_[cookie_value['name']] = cookie_value['value']
    return dict_


def time_map(t_str, error=''):
    """
    >>>time_map('发布日期：2020年2月18日')
    2020-02-18
    """
    try:
        year, month, day = re.findall(r'(\d{4})\D(\d{1,2})\D(\d{1,2})', t_str)[0]
        return '{}-{:0>2}-{:0>2}'.format(year, month, day)
    except:
        return error


def obj_first(obj, error=''):
    return obj[0] if obj else error


def get_html_content(response: scrapy.http.Response, con_xpath: str) -> str:
    """
    返回网页响应中的正文主体html代码
    :param response: 网页响应
    :param con_xpath: 正文的爬取范围  eg:'//*[@id="mainText"]'
    :return: 正文主体html代码
    """
    html_content = response.xpath(con_xpath).get()
    html_content = re.sub(r'<script>[\s\S]*?</script>|\<\!--[\s\S]*?--\>|<style[\s\S]*?</style>', '', html_content)
    return re.sub(r'<([a-z]+)[\s\S]*?>', r'<\1>', html_content)


def query2dict(url):
    """
     >>>url = 'http://www.zjwjw.gov.cn/col/col1202101/index.html?uid=4978845&pageNum=1'
     >>>query2dict(url)
     {'uid': '4978845', 'pageNum': '1'}
    """
    return {k: obj_first(v) for k, v in parse_qs(urlparse(url).query).items()}


def parse2query(parse_data=None, url_join='', url_replace=''):
    query = urlencode(parse_data)
    if url_join:
        return url_join + query
    elif url_replace:
        return re.sub(r'\?.*', '?{}'.format(query), url_replace)
    else:
        return query


def xpath_from_remove(response: scrapy.http.Response, xpath_str):
    """获取xpath_str部分的页面数据（移除script和style节点的干扰）"""
    content = HTML(response.text)
    for dom in content.xpath('//script'):
        new_content = dom.getparent()
        new_content.remove(dom)
    for dom in content.xpath('//style'):
        new_content = dom.getparent()
        new_content.remove(dom)
    return re.sub(r'\<\!--[\s\S]*?--\>', '', content.xpath(xpath_str).strip())


def effective(start, end):
    if not start:
        return ''
    end = time_map(end, error='9999-12-31')
    start = time_map(start, error='1000-01-01')
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    if now < start:
        return '尚未生效'
    elif start <= now < end:
        return '现行有效'
    else:
        return '失效'


def find_effective_start(content, publish_time):
    return time_map(obj_first(re.findall(r'[自从]\d{4}\D\d{1,2}\D\d{1,2}\D{0,5}(?:实施|施行)', content)), error=publish_time)


class PageHTMLControl:
    """
    翻页器： pageControl(4, 2, "index", "shtml", 10, 'pages-nav');
             http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/zy/index_2.shtml
    """
    def __init__(self, response: str, re_str='createPageHTML(.*?);', count=False):
        # createPageHTML(89, 1,"index", "shtml",  "black2",621);
        self.find = re.findall(r'{}'.format(re_str), response)
        try:
            if count:
                self.total, self.count, self.now, self.default, self.type, *_ = eval(self.find[0])
            else:
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


class PageFormControl:
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


class GovBeiJingPageControl:
    """
    翻页器： Pager({size:266, current:0, prefix:'index',suffix:'html'});
             http://www.beijing.gov.cn/zhengce/zhengcefagui/index_1.html
    """
    def __init__(self, response):
        try:
            self.find = re.findall(r'Pager\(\{.*?\}\)\;', response)[0]
            self.total = int(re.findall(r'size\:(\d+)', self.find)[0])
            self.now = int(re.findall(r'current\:(\d+)', self.find)[0])
            self.default = re.findall(r'prefix\:\'(.*?)\'', self.find)[0]
            self.type = re.findall(r'suffix\:\'(.*?)\'', self.find)[0]
        except:
            self.find = self.total = self.now = self.default = self.type = None

    def next_page(self, url):
        if not self.find:
            return None
        elif self.total - 1 > self.now:
            base_url = url.split('/')
            base_url[-1] = '{}_{}.{}'.format(self.default, self.now + 1, self.type)
            return '/'.join(base_url)
        else:
            return None


class RedisConnect:
    def __init__(self):
        pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
        self.conn = redis.StrictRedis(connection_pool=pool)
        print('redis connect success')


class TimeShow:
    @staticmethod
    def to_second(time_str):
        second = 0
        try:
            m, s = time_str.split(':')
            second = int(m) * 60 + int(s)
        except:
            pass
        return second

    @staticmethod
    def to_min_second(time_str):
        min_second = '0'
        try:
            time_str = int(time_str)
            m = time_str // 60
            s = time_str % 60
            min_second = '{:0>2}:{:0>2}'.format(m, s)
        except:
            pass
        return min_second

    def median(self, time_list):
        time_median = sorted(self.to_second(i) for i in time_list)
        return self.to_min_second(time_median[1])


if __name__ == '__main__':
    # ts = TimeShow()
    # print(ts.median(['00:30', '10:21', '01:51']))
    print(find_effective_start('政策从2020年10月111日起正式施行', '2020-10-11'))
