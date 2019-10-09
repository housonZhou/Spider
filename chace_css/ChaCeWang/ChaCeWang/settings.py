# -*- coding: utf-8 -*-

# Scrapy settings for ChaCeWang project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'ChaCeWang'

SPIDER_MODULES = ['ChaCeWang.spiders']
NEWSPIDER_MODULE = 'ChaCeWang.spiders'

FONT_FILE = r'C:\Users\17337\Downloads\ccw.ttf'
FONT_LIST = [
    ' ', '9', '8', '3', '4', '7', '5', '&', '>', 'c', 'H', 'q', 'S', '#', 'G', 'h', 'E', 'g', 'x', '(', ')', 'R', '/',
    'u', 'r', 'd', '=', 'v', 'j', 'Q', 'V', 'i', 'N', 'B', 'T', '$', 'C', 'n', '!', 'p', 's', 'I', '|', 'L', 'F', '%',
    'b', '@', 'y', 'Y', '?', '_', 'f', '^', 'Z', 'l', '<', 'a', 'o', 'P', 'm', 't', 'W', 'U', 'O', 'A', 'J', 'M', 'e',
    'D', 'k', 'z', 'K', 'w', '+', '河', '精', '质', '据', '从', '收', '升', '安', '码', '受', '创', '易', '行', '年',
    '自', '步', '备', '措', '知', '企', '心', '龙', '因', '集', '限', '及', '列', '配', '专', '贸', '政', '东', '快',
    '号', '利', '公', '先', '等', '研', '称', '李', '山', '进', '改', '二', '度', '一', '立', '书', '注', '下', '火',
    '司', '机', '子', '条', '电', '甲', '家', '物', '设', '济', '栋', '助', '励', '天', '策', '小', '五', '光', '当',
    '有', '乡', '报', '县', '才', '督', '元', '计', '更', '违', '未', '者', '予', '请', '个', '四', '评', '证', '体',
    '格', '处', '册', '维', '发', '服', '深', '阅', '民', '信', '十', '广', '座', '丙', '云', '中', '任', '首', '华',
    '单', '道', '保', '万', '事', '新', '项', '与', '询', '术', '提', '件', '股', '扶', '源', '微', '张', '范', '围',
    '王', '委', '六', '理', '厂', '展', '八', '数', '金', '湖', '属', '罪', '通', '互', '管', '跑', '丁', '获', '资',
    '型', '网', '授', '值', '街', '算', '包', '准', '经', '名', '给', '并', '基', '地', '工', '复', '原', '息', '批',
    '园', '点', '过', '西', '来', '额', '免', '间', '符', '需', '务', '持', '部', '能', '活', '已', '国', '程', '得',
    '镇', '或', '域', '总', '水', '再', '的', '括', '时', '市', '验', '合', '文', '拆', '犯', '产', '错', '百', '学',
    '重', '辖', '为', '九', '除', '千', '费', '效', '量', '积', '订', '不', '规', '门', '造', '区', '月', '施', '员',
    '制', '也', '圳', '七', '还', '省', '联', '位', '北', '建', '革', '南', '监', '查', '字', '究', '阳', '须', '全',
    '导', '会', '大', '份', '日', '厅', '亿', '环', '法', '贴', '币', '类', '科', '申', '技', '城', '别', '海', '标',
    '目', '乙', '纸', '主', '三', '优', '图', '所', '商', '州', '刘', '种', '变', '奖', '秀', '补', '京', '高', '人',
    '运', '2', '1', '6', '*', '~', '±', 'X', '业', '院', '⚪', '明', '局', '第'
]
PROJECT_TYPE = {
    'High-Tech': '总经圳据册第',
    'ESAER': '节水减排',
    'MajorProject': '五员精值',
    'EquityFinancing': '括权配复',
    'ExAnteFunding': '京前配复',
    'SATA': '张圳资改',
    'BySupport': '程套配复',
    'AfterTheFund': '京后配复',
    'LaunchAid': '导获配复',
    'LIDB': '贷款再升再金',
    'Attract': '招主引配',
    'ScaleUp': '扩委上小模',
    'Srtp': '张导订精',
    'InnovativePlatform': '标经载环',
    'HQHeadquarte': '贴数册第',
    'EventsPlanner': '司动革划',
    'LittleMicro': '间格李册第',
    'LargeEnterprises': '员批册第',
    'Agency': '间介机属',
    'NGO': '社园组织',
    'ManufachuringMoney': '委第山码',
    'AppliedModel': '应用示立',
    'Standardization': '知全化',
    'TechnicalReform': '圳据地心',
    'CCIA': '委第阳盟',
    'RisingEconomy': '经兴委第',
    'Industries': '传统委第',
    'CITL': '除别份流',
    'RADOP': '导获间试',
    'Manufacturing': '委第化',
    'TIAF': '罪光认定究配复',
    'BAMD': '品牌究网场开拓',
    'IPR': '才识委权',
    'InformationAndIntegration': '集升化>两化融为',
}
CITY_PATH = r'C:\Users\17337\houszhou\data\SpiderData\查策网\city_info.xlsx'
CITY = {
    '上海': 'RegisterArea_ZXS_Shanghai',
    '北京': 'RegisterArea_ZXS_Beijing',
    '广州': 'RegisterArea_HNDQ_Guangdong_Guangzhou',
    '杭州': 'RegisterArea_HDDQ_Zhejiang_HangZhou',
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
}
COOKIES = {
    'Hm_lvt_42c061ff773ed320147f84a5220d9dcc': '1569575889,1569577851,1569650523',
    'Hm_lvt_f9b4d143305c6f75248d93b7b5d8f6f1': '1569575889,1569577851,1569650523',
    'nb-referrer-hostname': 'www.chacewang.com',
    'ASP.NET_SessionId': 'bepurveyxtwpnny2ycl5kmfo',
    'currentCity': '5a3209b2-f868-47fa-862a-15f5c1f950f4',
    'nb-start-page-url': 'http%3A%2F%2Fwww.chacewang.com%2FProjectSearch%2FCopyIndex%3Fcitycode%3DRegisterArea_HNDQ_Guangdong_SZ%26searchText%3D',
    'Hm_lpvt_42c061ff773ed320147f84a5220d9dcc': '1569803125',
    'Hm_lpvt_f9b4d143305c6f75248d93b7b5d8f6f1': '1569803125'
}
SAVE_PATH = r'C:\Users\17337\houszhou\data\SpiderData\查策网\now\查策网_广州_1452.{}'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'ChaCeWang (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

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
#    'ChaCeWang.middlewares.ChacewangSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'ChaCeWang.middlewares.ChacewangDownloaderMiddleware': 543,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'ChaCeWang.pipelines.ChacewangPipeline': 300,
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
