# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json

from intellectual_property.was_cnr_cn.was_cnr_cn.settings import SAVE_PATH


class WasCnrCnPipeline(object):
    def __init__(self):
        self.save_path = SAVE_PATH
        self.file = open(self.save_path, 'a', encoding='utf8')

    def __del__(self):
        self.file.close()

    def write_json(self, data):
        self.file.write(json.dumps(data, ensure_ascii=False) + '\n')
        self.file.flush()

    def process_item(self, item, spider):
        save_data = dict(item)
        self.write_json(save_data)
        return item
