# coding: utf-8
# Author：houszhou
# Date ：2020/5/7 16:51
# Tool ：PyCharm

import datetime
import hashlib
import os
import re
import json
from copy import deepcopy

import scrapy

from policy_reform.items import PolicyReformItem, extension_default
from policy_reform.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, PRINT_ITEM, IMG_ERROR_TYPE
from policy_reform.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    PageHTMLControl, find_effective_start

conn = RedisConnect().conn


class GovChongQingSpider(scrapy.Spider):
    name = 'GovChongQingSpider'

    project_hash = 'pr0414'
    website = '重庆市人民政府'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.cq.gov.cn/zwgk/fdzdgknr/lzyj/xzgfxwj/szf_38655/",
             "首页-政务公开-法定主动公开内容-履职依据-行政规范性文件-市政府", "人民政府-重庆-市政府", "政府文件"),
            ("http://www.cq.gov.cn/zwgk/fdzdgknr/lzyj/xzgfxwj/szfbgt_38656/",
             "首页-政务公开-法定主动公开内容-履职依据-行政规范性文件-市政府办公厅", "人民政府-重庆-市府办公厅", "政府文件"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, source_module, category, classify in urls:
            yield scrapy.Request(url, meta={"source_module": source_module, 'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        page_control = PageHTMLControl(response.text, re_str='createPage(.*?);')
        next_page = page_control.next_page(response.url)
        page_exists = response.xpath('//a[@class="overflow"]')
        for item in page_exists:
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, source_module + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, source_module + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        # print('next_page', next_page, meta)
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.guifan_style(response)

        # source_module = '-'.join(response.xpath('//ul[@class="breadcrumb"]/li//a/text()').extract())
        source_module = response.meta.get('source_module')
        # item = PolicyReformItem()
        # item['content'] = content
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        # item['title'] = title
        # item['file_type'] = file_type
        item['classify'] = response.meta.get('classify')
        # item['source'] = source
        item['category'] = response.meta.get('category')
        # item['publish_time'] = publish_time
        # item['html_content'] = html_content
        for index, file_name in enumerate(item['extension'].get('file_name')):
            file_url = item['extension'].get('file_url')[index]
            type_ = item['extension'].get('file_type')[index]
            if type_ == 'url':
                continue
            file_type = os.path.splitext(file_url.split('/')[-1])[-1]
            file_name_type = os.path.splitext(file_name)[-1]
            if (not file_name_type) or re.findall(r'[^\.a-zA-Z0-9]', file_name_type) or len(file_name_type) > 7:
                file_name = file_name + file_type
            meta = {'row_id': row_id, 'file_name': file_name}
            # print(response.url, file_url, file_name)
            yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download, dont_filter=True)

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        yield item

    def guifan_style(self, response):
        item = PolicyReformItem()
        index_no = theme = effective_start = title = source = effective_end = doc_no = write_time = publish_time = ''
        table = response.xpath('//table[@class="gkxl-top"]//td[@class="tit"]')
        for i in table:
            key = i.xpath('./text()').extract_first()
            key = re.sub(r'\s+', '', key)
            value = i.xpath('./following-sibling::td[1]/text()').extract_first()
            value = value.strip() if value else ''
            # print(key, value)
            if '索引号' in key:
                index_no = value
            elif '发布日期' in key:
                publish_time = time_map(value)
            elif '主题词' in key:
                theme = value
            elif '文号' in key:
                doc_no = value
            elif '生成日期' in key:
                write_time = time_map(value, error=value)
            elif '发布机构' in key:
                source = value
            elif '名称' in key:
                title = value

        source = source if source else self.website

        if not doc_no:
            file_type = ''
        elif '〔' in doc_no:
            file_type = obj_first(re.findall('^(.*?)〔', doc_no))
        elif '第' in doc_no:
            file_type = obj_first(re.findall('^(.*?)第', doc_no))
        elif obj_first(re.findall(r'^(.*?)\d', doc_no)):
            file_type = obj_first(re.findall(r'^(.*?)\d', doc_no))
        else:
            file_type = ''
        content_str = '//div[@class="gkxl-article"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            if (not url_) or re.findall(r'baidu|javascript', url_):
                continue
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            if re.findall(r'html|content_\d+', url_):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')

        attach_img = response.xpath('{}//img[not(@href="javascript:void(0);")]'.format(content_str))
        img_name = 'alt'
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
        extension['write_time'] = write_time
        extension['effective_start'] = effective_start
        extension['is_effective'] = effective(effective_start, effective_end)
        extension['effective_end'] = effective_end
        item['content'] = content
        item['title'] = title
        item['file_type'] = file_type
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

