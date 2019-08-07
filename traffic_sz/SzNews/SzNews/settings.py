# -*- coding: utf-8 -*-

# Scrapy settings for SzNews project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'SzNews'

SPIDER_MODULES = ['SzNews.spiders']
NEWSPIDER_MODULE = 'SzNews.spiders'

SAVE_PATH = r'C:\Users\17337\houszhou\data\SpiderData\深圳交通\深圳新闻网\json_new\szNews_{}.json'
ERROR_PATH = r'C:\Users\17337\houszhou\data\SpiderData\深圳交通\深圳新闻网\bad_data.json'
SEARCH_LIST = [
    '深圳 交通执法',
    '深圳 交通安全', '深圳 交通指挥', '深圳 交通管控', '深圳 交通违章',
    '深圳 交通疏导', '深圳 道路拥堵', '深圳 驾车', '深圳 交警', '深圳 违章停车', '深圳 公交车',
    '深圳 交通事故', '深圳 道路管制', '深圳 道路安全', '深圳 摩托车事故', '深圳 电瓶车事故', '深圳 闯红灯',
    '深圳 醉驾', '深圳 撞车', '深圳 司机', '深圳 三轮车', '深圳 吊销驾驶证', '深圳 地铁停运',
    '深圳 交通路线', '深圳 出行', '深圳 乘客', '深圳 客运', '深圳 营运车辆', '深圳 机动车',
    '深圳 出租车', '深圳 猎虎行动', '深圳 自行车', '深圳 道路施工', '深圳 倡导绿色出行', '深圳 车辆限高',
    '深圳 交通警察', '深圳 车道', '深圳 交通管理', '深圳 交通秩序', '深圳 驾驶员', '深圳 城市运输',
    '深圳 交通协管', '深圳 计程车', '深圳 行车记录仪', '深圳 泊车', '深圳 交通政策'
]
BAIDU_COOKIES = {
    'BAIDUID': 'ECF7AECD98C35911E98139FD57F63259:FG=1',
    'PSTM': '1565147172',
    'BIDUPSID': '28EE0944EFA5E7E16F0CEA6D866803D5',
    'BDORZ': 'B490B5EBF6F3CD402E515D22BCDA1598',
    'BD_UPN': '12314753',
    'delPer': '0',
    'BD_CK_SAM': '1',
    'PSINO': '6',
    'BDRCVFR[C0p6oIjvx-c]': 'I67x6TjHwwYf0',
    'H_PS_PSSID': '1426_21104_29523_29519_29098_29568_28830_29220_26350_29459_22157',
    'H_PS_645EC': '7d40XITzxIkusB20H2sEOZXeWFFiZWc5fY1D1JoOHwiq5UewML1h74EDjk0'
}
# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'SzNews (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 3

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
#    'SzNews.middlewares.SznewsSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'SzNews.middlewares.SznewsDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'SzNews.pipelines.SznewsPipeline': 300,
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

HTTPERROR_ALLOWED_CODES = [301, 302]
