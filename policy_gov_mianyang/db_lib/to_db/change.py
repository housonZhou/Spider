# coding: utf-8
# Author：houszhou
# Date ：2020/5/27 19:55
# Tool ：PyCharm
import datetime
import json
import os
import re
from collections import defaultdict

import pandas as pd

from db_lib.to_db.db2excel import to_excel
from db_lib.to_db.settings import Config
from db_lib.to_db.parse_file import parse_main

c = Config()
MODEL_EXCEL, SPIDER_EXCEL = c.MODEL_EXCEL, c.SPIDER_EXCEL


def change_file_name(file_json: str):
    """修改附件的字段"""
    file_json = json.loads(file_json)
    file_name = file_json.pop('file_name')
    file_type = file_json.pop('file_type')
    file_url = file_json.pop('file_url')
    new_json = file_json.copy()
    new_json['property_attachment#属性附件#file'] = []
    new_json['html_content#正文附件#file'] = []
    new_json['attachment#全文附件#file'] = []
    for index, name in enumerate(file_name):
        url = file_url[index]
        type_ = file_type[index]
        if type_ == 'url':
            new_json['attachment#全文附件#file'].append({'type': 'url', 'filename': name, 'url': url})
        else:
            new_json['attachment#全文附件#file'].append({'type': 'file', 'filename': name, 'url': url})
    return json.dumps(new_json, ensure_ascii=False)


def update_one(excel_path, new_path):
    from db_lib.extractdata.ExtratcGroup import Model
    print(excel_path)
    df = pd.read_excel(excel_path)

    content_head = 'content#数据原文#String'
    website_head = 'website#数据来源网站名#String'
    title_head = 'title#名称(标题)#String'
    source_head = 'source#信息来源#String'
    file_head = 'extension#扩展字段#json'

    record = defaultdict(list)

    for item in zip(df[content_head], df[website_head], df[title_head], df[source_head]):
        content, website, title, source = item
        new_source = source.split(';')[0] if isinstance(source, str) else source
        m = Model(source=new_source, website=website, title=title, content=content)
        result = m.get_all(string=True)
        if '国务院' == website and isinstance(source, str) and re.findall(r'国务院|中共中央', source):
            record['dept#部门(发布部门)#String'].append(source)
        else:
            record['dept#部门(发布部门)#String'].append(result.get('dept'))
        record['policy_level#层级(政策层级)#String'].append(result.get('level'))
        record['region#适用区域#String'].append(result.get('region'))
        record['human_group#适用对象#json'].append(result.get('group'))
        record['industry#适用产业#json'].append(result.get('industry'))
        record['profession#适用行业#json'].append(result.get('profession'))
    if 'human_group#适用对象#String' in df.columns.values:
        df.rename(columns={'human_group#适用对象#String': 'human_group#适用对象#json',
                           'industry#适用产业#String': 'industry#适用产业#json',
                           'profession#适用行业#String': 'profession#适用行业#json'}, inplace=True)

    for name, value in record.items():
        df[name] = value
    df[file_head] = df[file_head].apply(change_file_name)
    df.to_excel(new_path, index=False)


def zhengce(time_map):
    print('zhengce run')
    excel_dir = os.path.join(SPIDER_EXCEL, time_map)  # 原始excel
    new_dir = os.path.join(MODEL_EXCEL, time_map)  # 跑完模型excel
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)
    for item in os.listdir(excel_dir):
        excel_path = os.path.join(excel_dir, item)
        new_path = os.path.join(new_dir, item)
        update_one(excel_path, new_path)


def run_change():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    to_excel(today)  # 从数据库导出数据到excel
    zhengce(today)  # 数据跑模型，生成新的excel
    parse_main(today)  # 将模型数据转换入库


if __name__ == '__main__':
    run_change()
