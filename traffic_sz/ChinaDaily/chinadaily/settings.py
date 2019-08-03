# -*- coding: utf-8 -*-

# Scrapy settings for chinadaily project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'chinadaily'

SPIDER_MODULES = ['chinadaily.spiders']
NEWSPIDER_MODULE = 'chinadaily.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'chinadaily (+http://www.yourdomain.com)'

SEARCH_LIST = ['深圳 交通政策',
               '深圳 交通执法', '深圳 交通安全', '深圳 交通指挥', '深圳 交通管控', '深圳 交通违章',
               '深圳 交通疏导', '深圳 道路拥堵', '深圳 驾车', '深圳 交警', '深圳 违章停车', '深圳 公交车',
               '深圳 交通事故', '深圳 道路管制', '深圳 道路安全', '深圳 摩托车事故', '深圳 电瓶车事故', '深圳 闯红灯',
               '深圳 醉驾', '深圳 撞车', '深圳 司机', '深圳 三轮车', '深圳 吊销驾驶证', '深圳 地铁停运',
               '深圳 交通路线', '深圳 出行', '深圳 乘客', '深圳 客运', '深圳 营运车辆', '深圳 机动车',
               '深圳 出租车', '深圳 猎虎行动', '深圳 自行车', '深圳 道路施工', '深圳 倡导绿色出行', '深圳 车辆限高',
               '深圳 交通警察', '深圳 车道', '深圳 交通管理', '深圳 交通秩序', '深圳 驾驶员', '深圳 城市运输',
               '深圳 交通协管', '深圳 计程车', '深圳 行车记录仪', '深圳 泊车'
               ]

COOKIES = 'wdcid=49e60bb9634186a1; UM_distinctid=16c424954c7244-0afd405c30f78b-3a65460c-1fa400-16c424954c850b; ' \
          'U_COOKIE_ID=52c02f0fad7c0205365dc340b92ff73f; pt_s_37a49e8b=vt=1564480201281&cad=; pt_37a49e8b=uid=' \
          'HLvSJvAN85uu00kRi-Se0Q&nid=0&vid=havRu8jOUIoXFEAcACbobQ&vn=3&pvn=1&sact=1564556161954&to_flag=1&pl=' \
          't4NrgYqSK5M357L2nGEQCw*pt*1564556137539'
# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Mysql setting
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = '123pingan321'
MYSQL_DB = 'SpiderData'

# save file
SAVE_PATH = r'C:\Users\17337\houszhou\data\SpiderData\深圳交通\中国日报\0731_{}.json'
SAVE_LINE = 5000

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 10

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'chinadaily.middlewares.ChinadailySpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'chinadaily.middlewares.ChinadailyDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'chinadaily.pipelines.ChinadailyPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
