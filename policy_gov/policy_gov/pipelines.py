# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql

from policy_gov.items import PolicyReformItem
from policy_gov.settings import DB_INFO, RUN_LEVEL


class PolicyReformPipeline(object):
    def __init__(self):
        self.con = pymysql.connect(**DB_INFO)
        self.cur = self.con.cursor()

    def execute(self, sql, meta=None, result=False):
        self.cur.execute(sql, meta)
        if result:
            return self.cur.fetchall()

    @ staticmethod
    def insert_sql(keys):
        sql = "INSERT INTO zhengce_gov ({}) values ({})".format(', '.join(keys), ', '.join(['%s'] * len(keys)))
        return sql

    def process_item(self, item: PolicyReformItem, spider):
        if not item or not isinstance(item, PolicyReformItem):
            return item
        keys = item.keys()
        values = tuple(list(item.values()))
        self.execute(sql=self.insert_sql(keys), meta=values)
        if RUN_LEVEL == 'FORMAT':
            self.con.commit()
        # self.con.commit()
        return item

    def __del__(self):
        self.con.close()


if __name__ == '__main__':
    pass
