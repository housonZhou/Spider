from scrapy.cmdline import execute


def start_one():
    # spider_name = 'GovChongQingSpider'
    spider_name = 'GovJiangSuSpider'
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovChongQingSpider'
    execute('scrapy crawl {}'.format(spider_name).split())


def start_all():
    execute('scrapy crawlall'.split())


start_all()
