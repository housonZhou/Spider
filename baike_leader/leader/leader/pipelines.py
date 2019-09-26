# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import pandas as pd
from baike_leader.leader.leader.settings import SAVE_EXCEL, SAVE_JSON


class LeaderPipeline(object):
    def __init__(self):
        self.file = open(SAVE_JSON, 'a', encoding='utf8')
        self.need_head = True

    def __del__(self):
        self.file.close()

    def process_item(self, item, spider):
        data = {'标题_百科': item.get('title'), '副标题_百科': item.get('subtitle'), '链接_百科': item.get('url'),
                '简介_百科': item.get('summary'), '人物履历_百科': item.get('time_resume', '[]')}
        data.update(item.get('info'))
        self.file.write(json.dumps(data, ensure_ascii=False) + '\n')
        self.file.flush()
        self.write_excel(data)
        return item

    def write_excel(self, data):
        to_list = []
        do_time = set()
        time_resume = json.loads(data.get('人物履历_百科'))
        time_resume = time_resume if time_resume else [{'time': '', 'do': ''}]
        for each in time_resume:
            new_data = data.copy()
            each_time = each.get('time')
            if each_time not in do_time:
                new_data['时间'] = each_time
                new_data['期间任职'] = each.get('do')
                to_list.append(new_data)
                do_time.add(each_time)
        df = pd.DataFrame(to_list)
        df.to_csv(SAVE_EXCEL, mode='a', encoding='utf8', index=False, header=self.need_head)
        self.need_head = 0
