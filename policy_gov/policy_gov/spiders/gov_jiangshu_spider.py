# coding: utf-8
# Author：houszhou
# Date ：2020/5/7 19:31
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
from policy_gov.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start, format_doc_no, format_file_type


class GovJiangSuSpider(scrapy.Spider):
    name = 'GovJiangSuSpider'
    base_url = 'http://www.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=25'

    project_hash = 'policy_gov0508'
    website = '江苏省人民政府'
    # classify = '政府文件'

    data = {
        'col': '1',
        'appid': '1',
        'webid': '1',
        'path': '/',
        'columnid': '76705',
        # 'sourceContentType': '3',
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
            (self.base_url.format(1, 75), "人民政府-江苏-省政府及办公厅文件", "政府文件",
             {'columnid': '76841', 'sourceContentType': '1', 'unitid': '297589'}),
            (self.base_url.format(1, 75), "人民政府-江苏-省政府规章", "地方行政规章",
             {'columnid': '76704', 'sourceContentType': '3', 'unitid': '297979'}),
            (self.base_url.format(1, 75), "人民政府-江苏-发展规划", "发展规划",
             {'columnid': '76732', 'sourceContentType': '1', 'unitid': '295574'}),
            (self.base_url.format(1, 75), "人民政府-江苏-政策解读", "部门解读",
             {'columnid': '76706', 'sourceContentType': '3', 'unitid': '297629'}),
            (self.base_url.format(1, 75), "人民政府-江苏-政策图解", "部门解读",
             {'columnid': '76462', 'unitid': '300251'}),
            (self.base_url.format(1, 75), "人民政府-江苏-专项规划", "专项规划",
             {'columnid': '76733', 'sourceContentType': '1', 'unitid': '295574'}),
            (self.base_url.format(1, 75), "人民政府-江苏-空间规划", "专项规划",
             {'columnid': '76842', 'sourceContentType': '1', 'unitid': '295574'}),
            (self.base_url.format(1, 75), "人民政府-江苏-行动计划", "专项规划",
             {'columnid': '76844', 'unitid': '295574'}),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, category, classify, data in urls:
            post_data = self.data.copy()
            post_data.update(data)
            yield scrapy.FormRequest(url, formdata=post_data, callback=self.parse, headers=self.headers,
                                     meta={'category': category, 'classify': classify, 'data': data})

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        content = response.text
        data = response.meta.get('data')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"data": data, 'category': category, 'classify': classify}
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
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        print('next_page', next_url, meta)
        if next_url:
            post_data = self.data.copy()
            post_data.update(data)
            yield scrapy.FormRequest(next_url, formdata=post_data, callback=self.parse,
                                     headers=self.headers, meta=meta, dont_filter=True)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        if response.xpath('//table[@class="xxgk_table"]'):
            item = self.zhengce_style(response)
        else:
            item = self.news_style(response)
        if response.xpath('//table[@class="martop5"]//table//table').extract_first():
            word = response.xpath('string(//table[@class="martop5"]//table//table)').extract_first().split(' >> ')
        else:
            word = response.xpath('//div[@class="bt-position"]//table//a/text()').extract()
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        if category == '人民政府-江苏-省政府规章' and '人民代表大会' in item['title']:
            classify = '地方性法规'
        source_module = '-'.join(i.strip() for i in word if i.strip())
        doc_no = item['extension']['doc_no']
        doc_no = format_doc_no(doc_no)
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
            if not file_name:
                file_name = file_url.split('/')[-1]
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

    def zhengce_style(self, response):
        item = PolicyReformItem()
        write_time = effective_start = effective_end = exclusive_sub = ''
        title = response.xpath('string(//table[@class="xxgk_table"]/tbody/tr[3]/td[2])').extract_first().strip()
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
        exclusive_sub = response.xpath('//table[@class="xxgk_table"]/tbody/tr[1]/td[4]/text()').extract_first()
        exclusive_sub = exclusive_sub.strip() if exclusive_sub else ''
        content_str = '//*[@id="zoom"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        fujian_str = '//ul[@class="xgbd"]'
        attach_str = '{}//a[not(@href="javascript:void(0);")]'
        attach = response.xpath('{}|{}'.format(attach_str.format(content_str), attach_str.format(fujian_str)))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first(default='').strip()
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
        img_name = 'none'
        for a in attach_img:
            file_name = a.xpath('./@{}'.format(img_name)).extract_first(default='').strip()
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

    def news_style(self, response):
        item = PolicyReformItem()
        write_time = effective_start = effective_end = doc_no = index_no = theme = exclusive_sub = ''
        title = response.xpath('string(//div[@class="sp_title"])').extract_first(default='').strip()
        other = response.xpath('string(//div[@class="sp_time"])').extract_first(default='').strip()
        source = obj_first(re.findall(r'来源：(\S*)', other))
        publish_time = time_map(other)

        content_str = '//*[@id="zoom"]'
        fujian_str = '//ul[@class="xgbd"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach_str = '{}//a[not(@href="javascript:void(0);")]'
        attach = response.xpath('{}|{}'.format(attach_str.format(content_str), attach_str.format(fujian_str)))
        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first(default='').strip()
            url_ = a.xpath('./@href').extract_first()
            download_url = response.urljoin(url_)
            if (not url_) or re.findall(r'baidu|javascript', url_):
                continue
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            if re.findall(r'htm|ewT\.aspx\?', url_):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')

        attach_img = response.xpath('{}//img[not(@href="javascript:void(0);")]'.format(content_str))
        img_name = 'none'
        for a in attach_img:
            file_name = a.xpath('./@{}'.format(img_name)).extract_first(default='').strip()
            url_ = a.xpath('./@src').extract_first()
            if not url_ or url_.split('.')[-1].lower() in IMG_ERROR_TYPE or re.findall(r'jslib|picture|\{.*?\}', url_):
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
