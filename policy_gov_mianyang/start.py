import subprocess

from scrapy.cmdline import execute


def start_one():
    # spider_name = 'GovChongQingSpider'
    # spider_name = 'GovShangHaiSpider'
    # spider_name = 'GovBeiJingSpider'
    # spider_name = 'GovGuangZhouSpider'
    # spider_name = 'GovShenZhenSpider'
    # spider_name = 'GovGuangDongSpider'
    # spider_name = 'GovJiangSuSpider'
    # spider_name = 'GovChongQingSpider'
    spider_name = 'GovSpider'
    # spider_name = 'GovSiChuanSpider'
    # spider_name = 'GovZheJiangSpider'

    execute('scrapy crawl {}'.format(spider_name).split())


def start_all():
    execute('scrapy crawlall'.split())


def update_content():
    import pymysql
    import json
    from policy_gov_mianyang.settings import DB_INFO
    table = 'BIZ_GMESP_PLCY'
    date = '2020-05-29'
    conn = pymysql.connect(**DB_INFO)
    cur = conn.cursor()
    select_sql = """select ID,CONTENT from {} where CREATE_DATE > '{}'""".format(table, date)
    update_sql = """update %s set content = '%s' where id = '%s'"""
    cur.execute(select_sql)
    for id_, content in cur.fetchall():
        try:
            content_list = json.loads(content)
            new_content = '\r\n'.join(content_list)
        except Exception as e:
            print(e)
            continue
        print(content, new_content)
        try:
            cur.execute(update_sql, meta=(table, new_content, id_))
            conn.commit()
        except:
            conn.rollback()
            print(cur.mogrify(update_sql, (table, new_content, id_)))
        break
    conn.close()



start_one()
