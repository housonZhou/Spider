# -*- coding: utf-8 -*-
import json
from traffic_sz.ChinaNews.ChinaNews.settings import SAVE_PATH, SEARCH_LIST
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ChinanewsPipeline(object):
    def __init__(self):
        self.file_list = {'error': open(SAVE_PATH.format('error'), 'a', encoding='utf8')}
        for search_name in SEARCH_LIST:
            file = open(SAVE_PATH.format(search_name), 'a', encoding='utf8')
            self.file_list[search_name] = file

    def __del__(self):
        for name, file in self.file_list.items():
            file.close()

    def process_item(self, item, spider):
        search_word = item.get('search_word')
        if search_word not in self.file_list:
            search_word = 'error'
        file = self.file_list[search_word]
        try:
            file.write(json.dumps(dict(item), ensure_ascii=False) + '\n')
            file.flush()
        except Exception as e:
            print(e)
        return item
