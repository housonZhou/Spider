# -*- coding: utf-8 -*-

# Scrapy settings for ChinaNews project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'ChinaNews'

SPIDER_MODULES = ['ChinaNews.spiders']
NEWSPIDER_MODULE = 'ChinaNews.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'ChinaNews (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False


# request default
END_SEARCH_TIME = '2009-01-01'
SAVE_PATH = r'C:\Users\17337\houszhou\data\SpiderData\深圳交通\中国新闻网\json\0802_{}.json'
SEARCH_LIST = [
    '深圳 交通执法',
    # '深圳 交通安全', '深圳 交通指挥', '深圳 交通管控', '深圳 交通违章',
    # '深圳 交通疏导', '深圳 道路拥堵', '深圳 驾车', '深圳 交警', '深圳 违章停车', '深圳 公交车',
    # '深圳 交通事故', '深圳 道路管制', '深圳 道路安全', '深圳 摩托车事故', '深圳 电瓶车事故', '深圳 闯红灯',
    # '深圳 醉驾', '深圳 撞车', '深圳 司机', '深圳 三轮车', '深圳 吊销驾驶证', '深圳 地铁停运',
    # '深圳 交通路线', '深圳 出行', '深圳 乘客', '深圳 客运', '深圳 营运车辆', '深圳 机动车',
    # '深圳 出租车', '深圳 猎虎行动', '深圳 自行车', '深圳 道路施工', '深圳 倡导绿色出行', '深圳 车辆限高',
    # '深圳 交通警察', '深圳 车道', '深圳 交通管理', '深圳 交通秩序', '深圳 驾驶员', '深圳 城市运输',
    # '深圳 交通协管', '深圳 计程车', '深圳 行车记录仪', '深圳 泊车', '深圳 交通政策'
]
HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/'
              'signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Length': '141',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'sou.chinanews.com',
    'Origin': 'http://sou.chinanews.com',
    'Referer': 'http://sou.chinanews.com/search.do',
    'Upgrade-Insecure-Requests': '1',
}
COOKIES = {
    'BAIDU_SSP_lcr': 'http://www.ce.cn/',
    'Hm_lpvt_0da10fbf73cda14a786cd75b91f6beab': '1564733534',
    'Hm_lvt_0da10fbf73cda14a786cd75b91f6beab': '1564653221',
    'JSESSIONID': 'aaaEmbPDwSGvygoCws9Ww',
    'UM_distinctid': '16c4247ccc946f-0cd64eafbd7fd4-3a65460c-1fa400-16c4247ccca294',
    '_Jo0OQK': '117B0629A2FEEF486E5680750266E4A7565BC52D731174FA0203A39DD88718C03BA7D8B4CD0B987224E7A9A68A8E1695EA3F4'
               '2A16DCEBDCC5E00F08715F73728923600AE3561610F31BE27B08D844972DF5E27B08D844972DF5F3E01977C89B6537B011693'
               '80683CBEDGJ1Z1SQ==',
    '__jsluid_h': '074290a55da18d1b284535f404dfca15',
    'cnsuuid': '71a4b555-79c7-4ff9-882b-b019f403aef66121.34160506955_1564396031348',
    'zycna': 'TJmFCNBrITYBAdoRcL9IUdYe'
}
POST_DATA = {
    'q': '',
    'ps': '100',
    'start': '0',
    'type': '',
    'sort': 'pubtime',
    'time_scope': '0',
    'channel': 'all',
    'adv': '1',
    'day1': '',
    'day2': '',
    'field': 'content',
    'creator': ''
}


# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 6

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'ChinaNews.middlewares.ChinanewsSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'ChinaNews.middlewares.ChinanewsDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'ChinaNews.pipelines.ChinanewsPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
