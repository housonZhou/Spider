# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import re
import requests
import scrapy
import json
from scrapy import signals
from StatsGov.settings import POST_HEADERS
from tools.base_code import parse2query
from StatsGov.spiders.stats_gov import StatsGovSpider
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


option = ChromeOptions()
option.add_experimental_option('excludeSwitches', ['enable-automation'])
# option.add_argument('--headless')


class CookiesMiddleware(object):
    def __init__(self):
        self.cookies = self.get_driver_cookies()
        self.proxy = self.get_proxies()

    @staticmethod
    def get_driver_cookies():
        driver = webdriver.Chrome(options=option)
        url = 'http://data.stats.gov.cn/easyquery.htm?cn=C01'
        driver.get(url)
        driver.implicitly_wait(10)
        cookies = driver.get_cookies()
        dict_ = {}
        for i in range(len(cookies)):
            cookie_value = cookies[i]
            dict_[cookie_value['name']] = cookie_value['value']
        print('重新获取cookies:', dict_)
        return dict_

    def reset_time(self):
        for k, v in StatsGovSpider.code_json.items():
            wds = '[{"wdcode":"reg","valuecode":"110000"}]' if '主要城市' in k else '[]'
            req_data = {'m': 'QueryData', 'dbcode': v, 'rowcode': 'zb', 'colcode': 'sj', 'wds': wds,
                        'dfwds': '[{"wdcode":"sj","valuecode":"2010-"}]'}
            url = parse2query(req_data, url_join=StatsGovSpider.url_query)
            print('设置访问时间')
            resp = requests.get(url, headers=POST_HEADERS, cookies=self.cookies)
            print(resp.status_code)

    @staticmethod
    def get_proxies():
        """获取代理"""
        proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host": '222.185.28.38',
            "port": '6442',
            "user": '16HEOFQR',
            "pass": '404729',
        }
        return proxy_meta

    def process_request(self, request: scrapy.Request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        request.cookies = self.cookies
        request.meta['proxy'] = self.proxy
        # print(request.headers)
        print('request.cookies:', request.cookies)
        return None

    def process_response(self, request: scrapy.Request, response: scrapy.http.Response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        url = response.url
        if 'QueryData' in url:
            try:
                json.loads(response.body.decode())
            except:
                print('cookies失效:', request.cookies)
                print(response.body.decode())
                self.cookies = self.get_driver_cookies()
                self.reset_time()
                return request.copy()
        return response


class StatsgovSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class StatsgovDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


if __name__ == '__main__':
    CookiesMiddleware()