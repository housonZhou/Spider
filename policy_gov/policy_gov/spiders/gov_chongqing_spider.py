# coding: utf-8
# Author：houszhou
# Date ：2020/5/7 16:51
# Tool ：PyCharm

import datetime
import hashlib
import json
import os
import re
from copy import deepcopy

import scrapy

from policy_gov.items import PolicyReformItem, extension_default
from policy_gov.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_gov.util import RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    PageHTMLControl, find_effective_start, format_doc_no, format_file_type

conn = RedisConnect().conn


class GovChongQingSpider(scrapy.Spider):
    name = 'GovChongQingSpider'

    project_hash = 'policy_gov0508'
    website = '重庆市人民政府'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.cq.gov.cn/zwgk/fdzdgknr/lzyj/zfgz/zfgz_52609/",
             "首页-政务公开-法定主动公开内容-履职依据-政府规章-政府规章",
             "人民政府-重庆-政府规章", "地方行政规章"),
            ("http://www.cq.gov.cn/zwgk/fdzdgknr/lzyj/zfgz/fzhsxzfgz_52610/",
             "首页-政务公开-法定主动公开内容-履职依据-政府规章-废止和失效政府规章",
             "人民政府-重庆-废止和失效政府规章", "政府文件"),
            ("http://www.cq.gov.cn/zwgk/fdzdgknr/lzyj/xzgfxwj/fzhsxxzgfxwj_52611/",
             "首页-政务公开-法定主动公开内容-履职依据-行政规范性文件-废止和失效行政规范性文件",
             "人民政府-重庆-废止和失效行政规范性文件", "政府文件"),
            ("http://www.cq.gov.cn/zwgk/fdzdgknr/ghxx/zxgh/",
             "首页-政务公开-法定主动公开内容-规划信息-专项规划",
             "人民政府-重庆-专项规划", "专项规划"),
            ("http://www.cq.gov.cn/zwgk/fdzdgknr/ghxx/qygh/",
             "首页-政务公开-法定主动公开内容-规划信息-区域规划",
             "人民政府-重庆-区域规划", "专项规划"),
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
        item = self.guifan_style(response)

        source_module = response.meta.get('source_module')
        doc_no = item['extension']['doc_no']
        doc_no = format_doc_no(doc_no)
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        title = item['title']
        if category == '人民政府-重庆-政府规章' and \
                re.findall('[省市区]', title) and re.findall('人民代表大会|条例', title):
            classify = '地方性法规'
        elif '废止和失效' in category:
            item['extension']['is_effective'] = '已失效'
        item['extension']['doc_no'] = doc_no
        item['file_type'] = format_file_type(doc_no)
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        item['classify'] = classify
        item['category'] = category
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

    def guifan_style(self, response):
        item = PolicyReformItem()
        index_no = theme = effective_start = title = source = effective_end = doc_no = write_time = publish_time = ''
        exclusive_sub = ''
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
            elif '信息分类名称' in key:
                exclusive_sub = value
            elif '名称' in key:
                title = value

        source = source if source else self.website
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
        extension['is_effective'] = effective(effective_start, effective_end)
        extension['effective_end'] = effective_end
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

