import os
from collections import defaultdict

import pandas as pd
import pymysql

from db_lib.to_db.settings import Config
from policy_gov_mianyang.settings import DB_INFO, MYSQL_TABLE

c = Config()
SPIDER_EXCEL = c.SPIDER_EXCEL


class PolicyReformPipeline(object):
    def __init__(self):
        self.con = pymysql.connect(**DB_INFO)
        self.cur = self.con.cursor()

    def execute(self, sql, meta=None, result=False):
        self.cur.execute(sql, meta)
        if result:
            return self.cur.fetchall()

    def __del__(self):
        self.con.close()


def to_excel(date):
    print('to_excel: {}'.format(date))
    pp = PolicyReformPipeline()
    select_sql = """
    SELECT 
    `id`,
    `row_id`,
    `content`,
    `website`,
    `source_module`,
    `url`,
    `title`,
    `classify`,
    `source`,
    `file_type`,
    `category`,
    `publish_time`,
    `html_content`,
    `extension`,
    `create_time`,
    `update_time`
    FROM `{}` 
    WHERE create_time > '{}';
    """.format(MYSQL_TABLE, date)
    result = pp.execute(select_sql, result=True)
    write_json = defaultdict(list)
    for item in result:
        _, row_id, content, website, source_module, url, title, classify, source, file_type, category, publish_time, html_content, extension, *_ = item
        data = {
            'row_id#信息公告id#String': row_id,
            'content#数据原文#String': content,
            'website#数据来源网站名#String': website,
            'source_module#数据来源网址板块#String': source_module,
            'url#网页url#String': url,
            'title#名称(标题)#String': title,
            'classify#所属分类#String': classify,
            'source#信息来源#String': source,
            'file_type#效力级别#String': file_type,
            'category#所属类别#String': category,
            'publish_time#发布时间#String': publish_time,
            'html_content#html原文#String': html_content,
            'extension#扩展字段#json': extension,
        }
        write_json[website].append(data)
    save_dir = os.path.join(SPIDER_EXCEL, date)
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    for website, write_list in write_json.items():
        save_path = os.path.join(save_dir, '{}_{}.xlsx'.format(website, ''.join(date.split('-'))))
        df = pd.DataFrame(write_list)
        df.to_excel(save_path, index=False)


if __name__ == '__main__':
    to_excel('2020-05-19')
