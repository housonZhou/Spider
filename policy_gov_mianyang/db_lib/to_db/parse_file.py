#! gmesp_policy_spider-1.0.0/venv python3
# -*- coding: utf-8 -*-
# @Time     : 2020-5-19 10:51
# @Author   : EX-HEYANG002
# @FILE     : parse_file.py
# @IDE     : PyCharm

import datetime
import json
import os
from concurrent.futures.process import ProcessPoolExecutor

from db_lib.to_db.settings import Config
from db_lib.to_db.to_sql import PolicyDecodePipeline, PolicyPipeline, LawPipeline

c = Config()
MODEL_EXCEL = c.MODEL_EXCEL


def parse(time_map):
    from pathlib import Path
    import pandas as pd
    base_dir = MODEL_EXCEL
    path_dir = os.path.join(base_dir, time_map)
    path = Path(path_dir)
    datas = pd.DataFrame()
    for file in path.iterdir():
        data = pd.read_excel(file, 'Sheet1')
        datas = datas.append(data, ignore_index=True)
    return datas


def parse_attach_title(data):
    result = []
    for item in data:
        if item['type'] == 'file':
            result.append(item.get('filename'))
    return result


def parse_attach_url(data):
    result = []
    for item in data:
        if item['type'] == 'file':
            result.append(item.get('url'))
    return result


def parse_relevant_title(data):
    result = []
    for item in data:
        if item['type'] == 'url':
            result.append(item.get('filename'))
    if result:
        return result[0]
    return None


def parse_relevant_url(data):
    result = []
    for item in data:
        if item['type'] == 'url':
            result.append(item.get('url'))
    if result:
        return result[0]
    return None


def parse_main(time_map):
    df = parse(time_map)
    column_orm = {label: label.split('#')[0] for label in df.columns}
    df.rename(columns=column_orm, inplace=True)

    df['decode'] = df.classify.apply(lambda item: '解读' in item)
    df['law'] = df.classify.apply(lambda item: '法规' in item)
    df['extension'] = df['extension'].apply(lambda item: json.loads(item))
    df['attaches'] = df['extension'].apply(
        lambda item: item['property_attachment#属性附件#file'] + item['html_content#正文附件#file'] + item[
            'attachment#全文附件#file']
    )
    df['new_content'] = df['content'].str.split(r'\r\n')
    df['attach_title'] = df['attaches'].apply(parse_attach_title)
    df['file_urls'] = df['attaches'].apply(parse_attach_url)
    df['relevant_title'] = df['attaches'].apply(parse_relevant_title)
    df['relevant_url'] = df['attaches'].apply(parse_relevant_url)
    df['file_no'] = df['extension'].apply(lambda item: item['doc_no'])
    columns = {
        'title': 'title', 'content': 'new_content', 'publish_time': 'publish_date', 'html_content': 'content_html',
        'file_no': 'file_no', 'region': 'region', 'website': 'website', 'dept': 'publish_agency',
        'attach_title': 'attach_title', 'file_urls': 'file_urls', 'relevant_title': 'relevant_title',
        'relevant_url': 'relevant_url', 'url': 'web_link', 'new_content': 'content'
    }
    decode_columns = ['title', 'publish_date', 'website', 'publish_agency', 'web_link', 'region']
    df.rename(columns=columns, inplace=True)
    decode = df[df['decode'] == True]
    law = df[df['law'] == True]
    df = df[(df['decode'] == False) & (df['law'] == False)]
    new_df = df[list(columns.values())]
    new_decode = decode[decode_columns]
    new_law = law[decode_columns]
    policy_decode = PolicyDecodePipeline()
    law = LawPipeline()
    policy = PolicyPipeline()
    workers = os.cpu_count()

    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(policy_decode.process_item, new_decode.to_dict(orient='records'))

    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(law.process_item, new_law.to_dict(orient='records'))

    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(policy.process_item, new_df.to_dict(orient='records'))


if __name__ == '__main__':
    t = datetime.datetime.now().strftime('%Y-%m-%d')
    parse_main(t)
