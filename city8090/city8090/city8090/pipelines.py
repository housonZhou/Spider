# -*- coding: utf-8 -*-
import json
from setting import DOWNLOAD_PATH
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class City8090Pipeline(object):
    def __init__(self):
        self.file = open(DOWNLOAD_PATH, "w", encoding="utf8")

    def __del__(self):
        self.file.close()

    def process_item(self, item, spider):
        self.file.write(json.dumps(dict(item), ensure_ascii=False) + "\n")
        return item
