# coding: utf-8
# Author：houszhou
# Date ：2020/6/9 14:16
# Tool ：PyCharm
import datetime
import hashlib
import json
import os
import re
from copy import deepcopy

import scrapy
from lxml.etree import HTML

from policy_gov.items import PolicyReformItem, extension_default
from policy_gov.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_gov.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start, format_file_type, format_doc_no


class FgwBeiJingSpider(scrapy.Spider):
    name = 'FgwBeiJingSpider'

    project_hash = 'policy_gov0508'
    website = '北京市发展和改革委员会'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://fgw.beijing.gov.cn/fgwzwgk/zcgk/flfggz/fg/",
             "发改委-北京-法规", "行政法规"),
            ("http://fgw.beijing.gov.cn/fgwzwgk/ghjh/",
             "发改委-北京-规划计划", "发展规划"),
            ("http://fgw.beijing.gov.cn/fgwzwgk/zcgk/flfggz/gz/",
             "发改委-北京-规章", "部门规章"),
            ("http://fgw.beijing.gov.cn/fgwzwgk/zcgk/bwqtwj/",
             "发改委-北京-其他文件", "政府文件"),
            ("http://fgw.beijing.gov.cn/fgwzwgk/zcgk/bwgfxwj/",
             "发改委-北京-规范性文件", "政府文件"),
            ("http://fgw.beijing.gov.cn/fgwzwgk/zcjd/",
             "发改委-北京-政策解读", "部门解读"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, category, classify in urls:
            yield scrapy.Request(url, meta={"classify": classify, 'category': category},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"classify": classify, 'category': category}
        url = response.url
        pager = JsPage(response.text)
        next_page = pager.next_page(url)

        for item in response.xpath('//ul[@class="list"]/li/a'):
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        print('next_page', next_page, meta)
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.zhengce_style(response)

        source_module = '-'.join(
            response.xpath('//div[@class="station"]//a/text()|//div[@class="station"]//span/text()').extract())
        doc_no = item['extension']['doc_no']
        doc_no = format_doc_no(doc_no)
        item['extension']['doc_no'] = doc_no
        item['file_type'] = format_file_type(doc_no)
        classify = response.meta.get('classify')
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        category = response.meta.get('category')
        title = item['title']
        if (category == '发改委-北京-规章') and \
                re.findall(r'[省市区]', title) and re.findall(r'令|办法|规定|实施细则', title):
            classify = '地方行政规章'
        item['category'] = category
        item['classify'] = classify

        for index, file_name in enumerate(item['extension'].get('file_name')):
            file_url = item['extension'].get('file_url')[index]
            type_ = item['extension'].get('file_type')[index]
            if type_ == 'url':
                continue
            file_type = os.path.splitext(file_url.split('/')[-1])[-1]
            file_name_type = os.path.splitext(file_name)[-1]
            if (not file_name_type) or re.findall(r'[^\.a-zA-Z0-9]', file_name_type) or len(file_name_type) > 7:
                file_name = file_name + file_type
            file_name = "{}_{}".format(index, file_name)
            item['extension']['file_name'][index] = file_name
            meta = {'row_id': row_id, 'file_name': file_name}
            if RUN_LEVEL == 'FORMAT':
                yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download,
                                     dont_filter=True)
            else:
                pass
                # print(response.url, file_url, meta)

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        yield item

    def zhengce_style(self, response: scrapy.http.Response):
        item = PolicyReformItem()
        index_no = write_time = effective_start = effective_end = theme = ''
        title = response.xpath('//div[@class="content"]/div[@class="xl_title"]/text()').extract_first(
            default='').strip()
        doc_no = response.xpath('//div[@class="content"]/div[@class="xl_subtitle"]/text()').extract_first(
            default='').strip()
        message = response.xpath('string(//div[@class="content"]/div[@class="xl_title_sub clearfix"])').extract_first(
            default='')
        source = obj_first(re.findall(r'来源：\s*([^\s\|]*)\s*', message))
        publish_time = time_map(message)

        content_str = '//div[@class="content"]/div[@class="xl_content"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()

        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))
        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = response.urljoin(url_)
            if (not url_) or (download_url == response.url):
                continue
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

        js_attach = obj_first(re.findall(r'document\.write\(\'(.*?)\'', response.text))
        js_attach = HTML(js_attach)
        for a in js_attach.xpath('//a'):
            file_name = a.xpath('string(.)')
            url_ = obj_first(a.xpath('./@href'))
            download_url = response.urljoin(url_)
            if (not url_) or (download_url == response.url) or file_name.startswith('正文-'):
                continue
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            if re.findall(r'htm', url_):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')
        if not effective_start:
            effective_start = find_effective_start(content, publish_time)

        extension['doc_no'] = doc_no
        extension['index_no'] = index_no
        extension['theme'] = theme
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


class JsPage:
    """
    var currentPage = 1;//所在页从0开始
    var prevPage = currentPage-1//上一页
    var nextPage = currentPage+1//下一页
    var countPage = 22//共多少页
    """

    def __init__(self, response: str):
        try:
            self.find = True
            self.total = int(re.findall(r'var countPage \= (\d+)', response)[0])
            self.now = int(re.findall(r'var currentPage \= (\d+)', response)[0])
            self.default = 'index'
            self.type = 'htm'
        except:
            self.find = self.total = self.now = self.default = self.type = None
        # finally:
        #     print(self.find, self.total, self.now, self.default, self.type)

    def next_page(self, url):
        if not self.find:
            return None
        elif self.total - 1 > self.now:
            base_url = url.split('/')
            base_url[-1] = '{}_{}.{}'.format(self.default, self.now + 1, self.type)
            return '/'.join(base_url)
        else:
            return None
