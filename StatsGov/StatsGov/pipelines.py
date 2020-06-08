# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import re
import json
from StatsGov.settings import SAVE_DIR


class StatsgovPipeline(object):
    code_json = {
        '年度': 'hgnd',
        '季度': 'hgjd',
        '月度': 'hgyd',
        '主要城市月度': 'csyd',
        '主要城市年度': 'csnd'
    }

    def __init__(self):
        self.file_list = {file: open(os.path.join(SAVE_DIR, '{}.json'.format(file)), 'a', encoding='utf8')
                          for file in self.code_json}

    def process_item(self, item, spider):
        data = item.get('write_data')
        type_ = re.findall(r'^(.*?)指标', data.get('层级'))[0]
        file = self.file_list.get(type_)
        file.write(json.dumps(data, ensure_ascii=False) + '\n')
        return item

    def __del__(self):
        for file in self.file_list.values():
            file.close()
