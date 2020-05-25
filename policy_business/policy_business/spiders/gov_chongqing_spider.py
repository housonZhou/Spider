# coding: utf-8
# Author：houszhou
# Date ：2020/5/22 14:37
# Tool ：PyCharm
import datetime
import hashlib
import json
import os
import re
import time
from copy import deepcopy
from lxml.etree import HTML
from urllib.parse import urljoin

import scrapy

from policy_business.items import PolicyReformItem, extension_default
from policy_business.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_business.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start, get_file_type

conn = RedisConnect().conn


class GovChongQingSpider(scrapy.Spider):
    name = 'GovChongQingSpider'

    project_hash = 'policy_business0520'
    website = '重庆市人民政府'
    model = '营商环境专题-政策集锦-{}'
    url = 'http://ccbapi.cqliving.com/tors/businessEnv/zh/policy/highlight.html?indicatorsCsv=&pageIndex={}&pageSize=20'
    detail_url = 'http://ccbapi.cqliving.com/tors/businessEnv/zh/policy/highlight/{}.html'
    show_url = 'http://cq.gov.cn/businesspc/#/detail?type=1&recId={}'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        url = self.url.format(1)
        meta = {'category': '营商环境-重庆-政策集锦', 'classify': '政府文件'}
        yield scrapy.Request(url, meta=meta, callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        category = response.meta.get('category')
        classify = response.meta.get('classify')
        meta = {'category': category, 'classify': classify}
        text = response.text
        text_json = json.loads(text)
        data = text_json.get('data')
        pager = data.get('PAGER')
        total_page = int(pager.get('PAGECOUNT', '0'))
        now_page = int(pager.get('CURRPAGE', '0'))
        if total_page > now_page:
            next_page = now_page + 1
        else:
            next_page = None

        for item in data.get('DATA'):
            rec_id = item.get('RECID')
            url = self.detail_url.format(rec_id)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + response.url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + response.url, 1)
            yield scrapy.Request(url, meta=meta, callback=self.parse_detail, headers=HEADERS)
        if next_page:
            url = self.url.format(next_page)
            # print(url)
            yield scrapy.Request(url, meta=meta, callback=self.parse, headers=HEADERS)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        extension = deepcopy(extension_default)
        text_json = json.loads(response.text)
        data = text_json.get('data')
        item = PolicyReformItem()
        classify = response.meta.get('classify')
        category = response.meta.get('category')

        index_no = theme = write_time = effective_end = ''
        rec_id = data.get('RECID')
        title = data.get('WJMC')
        html = data.get('ZCYW')
        html_content = re.sub(r'<([a-z]+)[\s\S]*?>', r'<\1>', html)
        content = xpath_from_remove(html, xpath_str='string(.)')
        model_label = data.get('YSHJ')
        source_module = self.model.format(model_label)
        doc_no = data.get('FWZH')
        file_type = get_file_type(doc_no)
        source = data.get('FWDW')
        publish_time = data.get('FWSJZD')
        exclusive_sub = data.get('ZCFL')
        effective_start = find_effective_start(content, publish_time)
        if re.findall(r'令|办法|规定|实施细则', title) and re.findall(r'[省市区]', title):
            classify = '地方行政规章'
        elif re.findall(r'令|办法|条例|规定|指导目录|纲要|规则|细则|准则', title):
            classify = '行政法规'
        elif re.findall(r'人民代表大会|条例', title) and re.findall(r'[省市区]', title):
            classify = '地方性法规'

        item['category'] = category
        item['classify'] = classify
        item['content'] = content
        item['row_id'] = row_id
        item['url'] = self.show_url.format(rec_id)
        item['title'] = title
        item['file_type'] = file_type
        item['source'] = source
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['website'] = self.website
        item['source_module'] = source_module
        extension['doc_no'] = doc_no
        extension['index_no'] = index_no
        extension['theme'] = theme
        extension['exclusive_sub'] = exclusive_sub
        extension['write_time'] = write_time
        extension['effective_start'] = effective_start
        extension['is_effective'] = effective(effective_start, effective_end)
        extension['effective_end'] = effective_end
        attach_img = HTML(html).xpath('//img[not(@href="javascript:void(0);")]')
        img_name = 'none'
        for a in attach_img:
            file_name = obj_first(a.xpath('./@{}'.format(img_name)))
            url_ = obj_first(a.xpath('./@src'))
            if not url_ or url_.split('.')[-1].lower() in IMG_ERROR_TYPE:
                continue
            if not file_name:
                file_name = url_.split('/')[-1]
            download_url = urljoin(self.show_url, url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            extension['file_type'].append('')
            meta = {'row_id': row_id, 'file_name': file_name}
            if RUN_LEVEL == 'FORMAT':
                yield scrapy.Request(download_url, meta=meta, headers=HEADERS, callback=self.file_download,
                                     dont_filter=True)
            else:
                print(response.url, download_url, meta)

        for file in data.get('FJ'):
            file_name = file.get('SRCFILE')
            file_url = file.get('PICURL')
            meta = {'row_id': row_id, 'file_name': file_name}
            extension['file_name'].append(file_name)
            extension['file_url'].append(file_url)
            if re.findall(r'htm', file_url):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')
            if RUN_LEVEL == 'FORMAT':
                yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download,
                                     dont_filter=True)
            else:
                print(response.url, file_url, meta)

        item['extension'] = json.dumps(extension, ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        yield item

    def file_download(self, response: scrapy.http.Response):
        file_io = response.body
        row_id = response.meta.get('row_id')
        file_name = response.meta.get('file_name')
        save_dir = os.path.join(self.date_dir, row_id)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        file_path = os.path.join(save_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_io)
        print('文件下载成功： ', file_path)
