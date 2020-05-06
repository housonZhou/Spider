from scrapy.cmdline import execute

spider_name = 'GovGuangDongSpider'
execute('scrapy crawl {}'.format(spider_name).split())
