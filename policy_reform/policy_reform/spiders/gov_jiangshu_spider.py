# coding: utf-8
# Author：houszhou
# Date ：2020/5/7 19:31
# Tool ：PyCharm

import datetime
import hashlib
import os
import re
import json
from copy import deepcopy

import scrapy

from policy_reform.items import PolicyReformItem, extension_default
from policy_reform.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_reform.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    GovBeiJingPageControl, find_effective_start


class GovJiangSuSpider(scrapy.Spider):
    name = 'GovJiangSuSpider'
    base_url = 'http://www.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=25'

    project_hash = 'pr0414'
    website = '江苏省人民政府'
    # classify = '政府文件'

    data = {
        'col': '1',
        'appid': '1',
        'webid': '1',
        'path': '/',
        'columnid': '76705',
        'sourceContentType': '3',
        'unitid': '297999',
        'webname': '江苏省人民政府',
        'permissiontype': '0'
    }
    headers = HEADERS.copy()
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'http://www.jiangsu.gov.cn/col/col76705/index.html',
        'X-Requested-With': 'XMLHttpRequest',
        # 'Cookie': 'JSESSIONID=612187F6B3FBC777127754650EE21D1F; __jsluid_h=9195ad95b72cad033aafbea19bfc2e4f; '
        #           'zh_choose_1=s; yunsuo_session_verify=62a80e4aa3e39238cbd35d48f19a53dc'
    })

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=75&perpage=25",
             "", "人民政府-江苏-行政规范文件", "政府文件"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, source_module, category, classify in urls:
            post_data = self.data.copy()
            yield scrapy.FormRequest(url, formdata=post_data, callback=self.parse, headers=self.headers,
                                     meta={"source_module": source_module, 'category': category, 'classify': classify})

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        content = response.text
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        start = int(obj_first(re.findall(r'startrecord=(\d+)', response.url)))
        end = int(obj_first(re.findall(r'endrecord=(\d+)', response.url)))
        total = int(obj_first(re.findall(r'<totalrecord>(\d+)</totalrecord>', content)))
        if end < total:
            next_url = self.base_url.format(start + 75, end + 75)
        else:
            next_url = ''
        #     page_exists = response.xpath('//ul[@class="uli14 pageList "]/li/a')
        for item in re.findall(r'href="(.*?)"', content):
            url = response.urljoin(item)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, source_module + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, source_module + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        # print('next_page', next_url, meta)
        if next_url:
            post_data = self.data.copy()
            yield scrapy.FormRequest(next_url, formdata=post_data, callback=self.parse,
                                     headers=self.headers, meta=meta, dont_filter=True)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.zhengce_style(response)
        word = response.xpath('string(//table[@class="martop5"]//table//table)').extract_first().split(' >> ')
        source_module = '-'.join(i.strip() for i in word if i.strip())
        # source_module = response.meta.get('source_module')
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
            # print(file_url, meta)
            yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download, dont_filter=True)

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        yield item

    def zhengce_style(self, response):
        item = PolicyReformItem()
        write_time = effective_start = effective_end = ''
        title = response.xpath('//table[@class="xxgk_table"]/tbody/tr[3]/td[2]/text()').extract_first().strip()
        source = response.xpath('//table[@class="xxgk_table"]/tbody/tr[2]/td[2]/text()').extract_first()
        source = source.strip() if source else ''
        doc_no = response.xpath('//table[@class="xxgk_table"]/tbody/tr[4]/td[2]/text()').extract_first()
        doc_no = doc_no.strip() if doc_no else ''
        publish_time = time_map(
            response.xpath('//table[@class="xxgk_table"]/tbody/tr[2]/td[4]/text()').extract_first())
        index_no = response.xpath('//table[@class="xxgk_table"]/tbody/tr[1]/td[2]/text()').extract_first()
        index_no = index_no.strip() if index_no else ''
        theme = response.xpath('//table[@class="xxgk_table"]/tbody/tr[4]/td[4]/text()').extract_first()
        theme = theme.strip() if theme else ''

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
        content_str = '//*[@id="zoom"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = response.urljoin(url_)
            if (not url_) or re.findall(r'baidu|javascript', url_):
                continue
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
            if (not url_) or len(url_) > 500 or (url_.split('.')[-1].lower() in IMG_ERROR_TYPE) or re.findall(
                    r'jslib|picture|\{.*?\}', url_):
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
        extension['effective_end'] = effective_end
        extension['is_effective'] = effective(effective_start, effective_end)
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
