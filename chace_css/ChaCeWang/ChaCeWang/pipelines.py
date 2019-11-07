# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json

from chace_css.ChaCeWang.ChaCeWang.settings import SAVE_PATH
from tools.base_code import Append2Excel as AExcel


class ChacewangPipeline(object):
    def __init__(self):
        self.save_path = SAVE_PATH
        self.excel_path = self.save_path.format('xlsx')
        self.file = open(self.save_path.format('json'), 'a', encoding='utf8')
        self.AExcel = AExcel(self.excel_path)

    def __del__(self):
        self.file.close()

    def write_json(self, data):
        self.file.write(json.dumps(data, ensure_ascii=False) + '\n')
        self.file.flush()

    def process_item(self, item, spider):
        save = item.get('save')
        info = save.get('info')
        result = item.get('result')
        save_data = {'城市': save.get('city'), '地区': save.get('area_name'), '项目类别': info.get('partition_real'),
                     '默认地区': save.get('default_area')}
        save_data.update(result)
        self.write_json(save_data.copy())
        self.AExcel.add(data=[save_data])
        return item
