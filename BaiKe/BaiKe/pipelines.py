# -*- coding: utf-8 -*-
import json
import pymysql
from .settings import *
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class BaikePipeline(object):
    def __init__(self):
        # mysql数据库用于储存词条url和summary数据
        self.db = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
                                  db=MYSQL_DB)
        self.cursor = self.db.cursor()
        # 四个不同的文件保存四种类型的数据
        self.file_list = {}
        for name, d_path in DOWNLOAD_PATH.items():
            file = open(d_path, "w", encoding="utf8")
            self.file_list[name] = file

    def __del__(self):
        for file in self.file_list.values():
            file.close()
        self.db.close()

    def process_item(self, item, spider):
        tag_name = item.get('tag')
        sql = "INSERT INTO baidubaike (url, summary)  values(%s, %s);"
        self.cursor.execute(sql, (item.get('url'), item.get('summary')))
        self.db.commit()

        file = self.file_list.get(tag_name)
        data_json = dict(item).copy()
        data_json.pop('summary')
        file.write(json.dumps(data_json, ensure_ascii=False) + "\n")
        file.flush()
        return item
