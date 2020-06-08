# coding: utf-8
# Author：houszhou
# Date ：2020/5/22 14:37
# Tool ：PyCharm
import datetime
import hashlib
import json
import os
import re
from copy import deepcopy
from urllib.parse import urljoin

import scrapy
from lxml.etree import HTML

from policy_business.items import PolicyReformItem, extension_default
from policy_business.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_business.util import obj_first, RedisConnect, xpath_from_remove, effective, \
    find_effective_start, query2dict, format_file_type, format_doc_no

conn = RedisConnect().conn


class GovChongQingSpider(scrapy.Spider):
    name = 'GovChongQingSpider'

    project_hash = 'policy_business0520'
    website = '重庆市人民政府'
    model = '营商环境专题-{}-{}'  # 营商环境专题-政策集锦-开办企业
    # 翻页链接
    url = {
        '政策集锦': 'http://ccbapi.cqliving.com/tors/businessEnv/zh/policy/highlight.html?indicatorsCsv={}&pageIndex={}&pageSize=20',
        '政策解读': 'http://ccbapi.cqliving.com/tors/businessEnv/policy/understanding.html?indicatorsCsv={}&pageIndex={}&pageSize=20',
        '政策图解': 'http://ccbapi.cqliving.com/tors/businessEnv/policy/schema.html?indicatorsCsv={}&pageIndex={}&pageSize=20'
    }
    # 详情页链接
    detail_url = {
        '政策集锦': 'http://ccbapi.cqliving.com/tors/businessEnv/zh/policy/highlight/{}.html',
        '政策解读': 'http://ccbapi.cqliving.com/tors/businessEnv/policy/understanding/{}.html',
        '政策图解': 'http://ccbapi.cqliving.com/tors/businessEnv/policy/schema/{}.html'
    }
    # 展示页面链接
    show_url = {
        '政策集锦': 'http://cq.gov.cn/businesspc/#/detail?type=1&recId={}',
        '政策解读': 'http://cq.gov.cn/businesspc/#/detail?type=2&recId={}',
        '政策图解': 'http://cq.gov.cn/businesspc/#/detail?type=3&recId={}'
    }
    indicators = ['开办企业', '办理施工许可', '获得电力', '登记财产', '获得信贷', '保护少数投资者',
                  '纳税', '跨境贸易', '执行合同', '办理破产', '政府采购', '综合']
    indicators_dict = dict(zip(indicators, range(1, 13)))

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        name_list = [
            '政策集锦',
            '政策解读',
            '政策图解',
        ]
        for name in name_list:
            for indicator, index in self.indicators_dict.items():
                url = self.url.get(name).format(index, 1)
                meta = {'category': '营商环境-重庆-{}'.format(name), 'classify': '政府文件',
                        'name': name, 'indicator': indicator}
                yield scrapy.Request(url, meta=meta, callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        category = response.meta.get('category')
        classify = response.meta.get('classify')
        name = response.meta.get('name')
        indicator = response.meta.get('indicator')
        meta = {'category': category, 'classify': classify, 'name': name, 'indicator': indicator}
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
            url = self.detail_url.get(name).format(rec_id)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + response.url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + response.url, 1)
            # print(url, meta)
            yield scrapy.Request(url, meta=meta, callback=self.parse_detail, headers=HEADERS)
        if next_page:
            index = self.indicators_dict.get(indicator)
            url = self.url.get(name).format(index, next_page)
            print(url)
            yield scrapy.Request(url, meta=meta, callback=self.parse, headers=HEADERS)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        text_json = json.loads(response.text)
        data = text_json.get('data')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        name = response.meta.get('name')
        indicator = response.meta.get('indicator')
        source_module = self.model.format(name, indicator)
        rec_id = obj_first(re.findall(r'\d+', response.url))
        data['RECID'] = rec_id

        if name == '政策集锦':
            item = self.policy(data, name)
        elif name == '政策解读':
            item = self.interpretation(data, name)
        else:
            item = self.pict(data, name)

        doc_no = item['extension']['doc_no']
        doc_no = format_doc_no(doc_no)
        item['extension']['doc_no'] = doc_no
        item['file_type'] = format_file_type(doc_no)

        if category == '营商环境-重庆-政策集锦':
            title = item.get('title')
            if re.findall(r'令|办法|规定|实施细则', title) and re.findall(r'[省市区]', title):
                classify = '地方行政规章'
            elif re.findall(r'令|办法|条例|规定|指导目录|纲要|规则|细则|准则', title):
                classify = '行政法规'
            elif re.findall(r'人民代表大会|条例', title) and re.findall(r'[省市区]', title):
                classify = '地方性法规'

        item['category'] = category
        item['classify'] = classify
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module

        for index, file_name in enumerate(item['extension'].get('file_name')):
            file_url = item['extension'].get('file_url')[index]
            type_ = item['extension'].get('file_type')[index]
            if type_ == 'url':
                continue
            if not file_name:
                file_name = file_url.split('/')[-1]
            file_type = os.path.splitext(file_url.split('/')[-1])[-1]
            file_name_type = os.path.splitext(file_name)[-1]
            if (not file_name_type) or re.findall(r'[^\.a-zA-Z0-9]', file_name_type) or len(file_name_type) > 7:
                file_name = file_name + file_type
            file_name = '{}_{}'.format(index, file_name)  # 加上索引，防止重复
            item['extension']['file_name'][index] = file_name
            meta = {'row_id': row_id, 'file_name': file_name}
            if RUN_LEVEL == 'FORMAT':
                yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download,
                                     dont_filter=True)
            else:
                print(response.url, file_url, meta)

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        yield item

    def policy(self, data, name):
        """政策"""
        item = PolicyReformItem()
        extension = deepcopy(extension_default)

        index_no = theme = write_time = effective_end = file_type = ''
        rec_id = data.get('RECID')
        title = data.get('WJMC')
        html = data.get('ZCYW')
        html_content = re.sub(r'<([a-z]+)[\s\S]*?>', r'<\1>', html)
        content = xpath_from_remove(html, xpath_str='string(.)')
        doc_no = data.get('FWZH')
        source = data.get('FWDW')
        publish_time = data.get('FWSJZD')
        exclusive_sub = data.get('ZCFL')
        effective_start = find_effective_start(content, publish_time)
        item['content'] = content
        item['url'] = self.show_url.get(name).format(rec_id)
        item['title'] = title
        item['file_type'] = file_type
        item['source'] = source
        item['publish_time'] = publish_time
        item['html_content'] = html_content
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

        for file in data.get('FJ'):
            file_name = file.get('SRCFILE')
            file_url = file.get('PICURL')
            extension['file_name'].append(file_name)
            extension['file_url'].append(file_url)
            if re.findall(r'htm', file_url):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')
        item['extension'] = extension
        return item

    def interpretation(self, data, name):
        """政策解读"""
        item = PolicyReformItem()
        extension = deepcopy(extension_default)

        index_no = theme = write_time = effective_end = file_type = doc_no = exclusive_sub = effective_start = ''
        rec_id = data.get('RECID')
        policy_id = data.get('POLICYID')
        policy_title = data.get('POLICYTITLE')
        title = data.get('ZCJDTITLE')
        html = data.get('ZCJDZW')
        html_content = re.sub(r'<([a-z]+)[\s\S]*?>', r'<\1>', html)
        content = xpath_from_remove(html, xpath_str='string(.)')
        source = data.get('FWDW', self.website)
        publish_time = data.get('FWSJZD')
        item['content'] = content
        item['url'] = self.show_url.get(name).format(rec_id)
        item['title'] = title
        item['file_type'] = file_type
        item['source'] = source
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['website'] = self.website
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

        if policy_id:
            file_name = policy_title
            file_url = self.show_url.get('政策集锦').format(policy_id)
            extension['file_name'].append(file_name)
            extension['file_url'].append(file_url)
            extension['file_type'].append('url')
        item['extension'] = extension
        return item

    def pict(self, data, name):
        """政策图解"""
        item = PolicyReformItem()
        extension = deepcopy(extension_default)

        index_no = theme = write_time = effective_end = file_type = doc_no = exclusive_sub = effective_start = ''
        html_content = content = ''
        rec_id = data.get('RECID')
        policy_id = data.get('POLICYID')
        policy_title = data.get('POLICYTITLE')
        title = data.get('ZCTJTITLE')
        source = data.get('FWDW', self.website)
        publish_time = data.get('FWSJZD')
        item['content'] = content
        item['url'] = self.show_url.get(name).format(rec_id)
        item['title'] = title
        item['file_type'] = file_type
        item['source'] = source
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['website'] = self.website
        extension['doc_no'] = doc_no
        extension['index_no'] = index_no
        extension['theme'] = theme
        extension['exclusive_sub'] = exclusive_sub
        extension['write_time'] = write_time
        extension['effective_start'] = effective_start
        extension['is_effective'] = effective(effective_start, effective_end)
        extension['effective_end'] = effective_end

        if policy_id:
            file_name = policy_title
            file_url = self.show_url.get('政策集锦').format(policy_id)
            extension['file_name'].append(file_name)
            extension['file_url'].append(file_url)
            extension['file_type'].append('url')

        for i in data.get('GRAPHICS'):
            graphic = i.get('GRAPHIC')
            pic_url = graphic.get('VALUE')
            extension['file_name'].append(pic_url.split('/')[-1])
            extension['file_url'].append(pic_url)
            extension['file_type'].append('')
        item['extension'] = extension
        return item

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
