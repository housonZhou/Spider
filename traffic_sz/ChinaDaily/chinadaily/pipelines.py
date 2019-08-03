# -*- coding: utf-8 -*-
import re
import json
import pymysql
from traffic_sz.chinadaily.chinadaily.settings import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, \
    SAVE_PATH, SEARCH_LIST
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ChinadailyPipeline(object):
    def __init__(self):
        # mysql数据库用于储存数据
        self.db = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD,
                                  db=MYSQL_DB)
        self.cursor = self.db.cursor()
        self.file_list = {'error': open(SAVE_PATH.format('error'), 'a', encoding='utf8')}
        for search_name in SEARCH_LIST:
            file = open(SAVE_PATH.format(search_name), 'a', encoding='utf8')
            self.file_list[search_name] = file

    def __del__(self):
        self.db.close()
        for name, file in self.file_list.items():
            file.close()

    def process_item(self, item, spider):
        search_word = re.sub('\+', ' ', item.get('search_word'))
        if search_word not in self.file_list:
            search_word = 'error'
        file = self.file_list[search_word]
        try:
            file.write(json.dumps(dict(item), ensure_ascii=False) + '\n')
            file.flush()
        except Exception as e:
            print(e)
        try:
            sql = "INSERT INTO chinadaily_traffic_sz " \
                  "(content, inner_id, key_word, search_word, source, time_map, title, url)  " \
                  "values(%s, %s, %s, %s, %s, %s, %s, %s);"
            self.cursor.execute(sql, (item.get('content'), item.get('inner_id'), item.get('key_word'),
                                      item.get('search_word'), item.get('source'), item.get('time_map'),
                                      item.get('title'), item.get('url')))
            self.db.commit()
        except Exception as e:
            print(e)
        return item
