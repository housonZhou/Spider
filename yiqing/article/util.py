#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/2/7 5:31 下午
# @Author  : Anson
# @Contact : 1047053860@qq.com
# @Software: PyCharm
# @content :
import re
import time
from selenium import webdriver
from lxml.etree import HTML
from selenium.webdriver import ChromeOptions
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

import scrapy

option = ChromeOptions()
option.add_experimental_option('excludeSwitches', ['enable-automation'])

gov_depts = ["卫生健康委网站"]


def return_tag(title, tag, source, level="国务院"):
    if "组织会" in title or "小组会" in title:
        return "%s-会议-组织会议" % level
    elif "常务会" in title:
        return "%s-会议-常务会议" % level
    elif "会议" in title:
        return "%s-会议-会议" % level
    elif "通知" in title:
        return "%s-政策文件-通知" % level
    elif "解读" in title and "《" in title:
        return "%s-政策文件-解读" % level
    elif "公告" in title:
        return "%s-政策文件-公告" % level
    elif source in gov_depts or "《" in title:
        return "%s-政策文件-其他" % level
    else:
        return tag


def return_tagz_wjw(title, level="国务院"):
    if "发布会" in title:
        return ""


def get_cookie(url):
    driver = webdriver.Chrome(options=option)
    driver.get(url)
    time.sleep(3)
    cookies = driver.get_cookies()
    print('cookies: ', cookies)
    driver.quit()
    items = []
    dict_ = {}
    for i in range(len(cookies)):
        cookie_value = cookies[i]
        item = cookie_value['name'] + '=' + cookie_value['value']
        items.append(item)
        dict_[cookie_value['name']] = cookie_value['value']
    cookiestr = '; '.join(a for a in items)
    # print(cookiestr)
    # return cookiestr
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
    :param con_xpath: 正文的爬取范围  eg:'//*[@id=""mainText]'
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
    content = HTML(response.text)
    for dom in content.xpath('//script'):
        new_content = dom.getparent()
        new_content.remove(dom)
    for dom in content.xpath('//style'):
        new_content = dom.getparent()
        new_content.remove(dom)
    return re.sub(r'\<\!--[\s\S]*?--\>', '', content.xpath(xpath_str).strip())


class PageHTMLControl:
    """
    翻页器： pageControl(4, 2, "index", "shtml", 10, 'pages-nav');
             http://www.hubei.gov.cn/zhuanti/2020/gzxxgzbd/zy/index_2.shtml
    """
    def __init__(self, response, re_str='createPageHTML(.*?);'):
        # createPageHTML(89, 1,"index", "shtml",  "black2",621);
        self.find = re.findall(r'{}'.format(re_str), response)
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
