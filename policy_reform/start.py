from scrapy.cmdline import execute

spider_name = 'GovBeiJingSpider'
execute('scrapy crawl {}'.format(spider_name).split())
