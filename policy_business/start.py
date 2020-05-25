from scrapy.cmdline import execute


def start_one():
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovShangHaiSpider'
    # spider_name = 'GovBeiJingSpider'
    # spider_name = 'GovGuangZhouSpider'
    # spider_name = 'GovShenZhenSpider'
    # spider_name = 'GovGuangDongSpider'
    # spider_name = 'GovJiangSuSpider'
    spider_name = 'GovChongQingSpider'
    # spider_name = 'GovSpider'
    # spider_name = 'GovSiChuanSpider'
    # spider_name = 'GovZheJiangSpider'

    execute('scrapy crawl {}'.format(spider_name).split())


def start_all():
    execute('scrapy crawlall'.split())


start_one()
