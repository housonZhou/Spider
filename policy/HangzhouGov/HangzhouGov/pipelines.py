# -*- coding: utf-8 -*-
import os
import json
import re
from policy.HangzhouGov.HangzhouGov.settings import JSON_PATH, SAVE_DIR
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class HangzhougovPipeline(object):
    def __init__(self):
        self.file = open(JSON_PATH, 'w', encoding='utf8')

    def __del__(self):
        self.file.close()

    def process_item(self, item, spider):
        file_title = re.sub('[\\\.\?\!\:\n\"\<\>\/\|]', '', item.get('title'))
        save_path = os.path.join(SAVE_DIR, f"{file_title}_{item.get('time_map')}.txt")
        with open(save_path, 'w', encoding='utf8', errors='ignore')as f:
            f.write('链接：\n{url}\n正文：\n{content}'.format(**item))
        self.file.write(json.dumps(dict(item), ensure_ascii=False) + '\n')
        self.file.flush()
        return item
