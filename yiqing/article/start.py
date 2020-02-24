from scrapy import cmdline

spider_name = 'ShangHaiWjwSpider'
cmdline.execute('scrapy crawl {}'.format(spider_name).split())
