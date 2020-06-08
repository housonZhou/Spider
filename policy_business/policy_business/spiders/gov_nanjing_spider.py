# coding: utf-8
# Author：houszhou
# Date ：2020/5/22 17:38
# Tool ：PyCharm

import datetime
import hashlib
import json
import os
import re
from copy import deepcopy

import scrapy

from policy_business.items import PolicyReformItem, extension_default
from policy_business.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_business.util import RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start, format_file_type, format_doc_no

conn = RedisConnect().conn


class GovNanJingSpider(scrapy.Spider):
    name = 'GovNanJingSpider'

    project_hash = 'policy_business0520'
    website = '南京市人民政府'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.nanjing.gov.cn/zt/jjnjscxmcjs/sxcs/yzkfbrdylhj/",
             "营商环境-南京-配套文件", "政府文件"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, category, classify in urls:
            yield scrapy.Request(url, meta={'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {'category': category, 'classify': classify}
        next_page = response.xpath('//*[@id="noshow"]/a[@class="next"]/@href').extract_first()
        page_exists = response.xpath('//div[@class="ptwj_left"]/a')
        for item in page_exists:
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        # print('next_page', next_page, meta)
        if next_page:
            # next_page = 'http://www.shanghai.gov.cn' + next_page
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.zhengce_style(response)

        source_module = "首页-专题-聚焦南京市创新名城建设-十项措施-营造开放包容的优良环境-配套文件"

        doc_no = item['extension']['doc_no']
        doc_no = format_doc_no(doc_no)
        item['extension']['doc_no'] = doc_no
        item['file_type'] = format_file_type(doc_no)
        category = response.meta.get('category')
        classify = response.meta.get('classify')
        if category == '营商环境-深圳-政策文件':
            title = item['title']
            if re.findall(r'令|办法|规定|实施细则', title) and re.findall(r'[省市区]', title):
                classify = '地方行政规章'
            elif re.findall(r'令|办法|条例|规定|指导目录|纲要|规则|细则|准则', title):
                classify = '行政法规'
            elif re.findall(r'人民代表大会|条例', title) and re.findall(r'[省市区]', title):
                classify = '地方性法规'
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        # item['title'] = title
        # item['file_type'] = file_type
        item['classify'] = classify
        # item['source'] = source
        item['category'] = category
        # item['publish_time'] = publish_time
        # item['html_content'] = html_content
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

    def zhengce_style(self, response):
        item = PolicyReformItem()
        exclusive_sub = index_no = theme = effective_start = doc_no = effective_end = source = write_time = ''
        title = response.xpath('//div[@class="title"]/text()').extract_first(default='').strip()
        other = response.xpath('string(//div[@class="time"])').extract_first(default='')
        publish_time = time_map(other)

        content_str = '//div[@class="content"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first(default='').strip()
            url_ = a.xpath('./@href').extract_first()
            if not url_ or 'share' in url_ or url_ == '#':
                continue
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            if re.findall(r'htm', url_):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')

        attach_img = response.xpath('{}//img[not(@href="javascript:void(0);")]'.format(content_str))
        img_name = 'none'
        for a in attach_img:
            file_name = a.xpath('./@{}'.format(img_name)).extract_first()
            url_ = a.xpath('./@src').extract_first()
            if not url_ or url_.split('.')[-1].lower() in IMG_ERROR_TYPE:
                continue
            if not file_name:
                file_name = url_.split('/')[-1]
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            extension['file_type'].append('')
        if not effective_start:
            effective_start = find_effective_start(content, publish_time)
        extension['doc_no'] = doc_no
        extension['index_no'] = index_no
        extension['theme'] = theme
        extension['exclusive_sub'] = exclusive_sub
        extension['write_time'] = write_time
        extension['effective_start'] = effective_start
        extension['effective_end'] = effective_end
        extension['is_effective'] = effective(effective_start, effective_end)
        item['content'] = content
        item['title'] = title
        item['source'] = source if source else self.website
        item['publish_time'] = publish_time
        item['html_content'] = html_content
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
