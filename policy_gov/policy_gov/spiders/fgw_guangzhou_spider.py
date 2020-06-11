# coding: utf-8
# Author：houszhou
# Date ：2020/6/10 11:14
# Tool ：PyCharm
import datetime
import hashlib
import os
import re
import json
from copy import deepcopy

import scrapy

from policy_gov.items import PolicyReformItem, extension_default
from policy_gov.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_gov.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start, format_doc_no, format_file_type

conn = RedisConnect().conn


class FgwGuangZhouSpider(scrapy.Spider):
    name = 'FgwGuangZhouSpider'

    project_hash = 'policy_gov0508'
    website = '广州市发展和改革委员会'
    base_url = 'http://fgw.gz.gov.cn/gkmlpt/api/all/{id}?page={page}&sid=200014'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://fgw.gz.gov.cn/tzgg/index.html", "发改委-广州-通知公告", "政府文件"),
            ("http://fgw.gz.gov.cn/fzgg/fzgh/index.html", "发改委-广州-发展规划", "发展规划"),
        ]
        for url, category, classify in urls:
            yield scrapy.Request(url, meta={'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)

        urls = [
            ({'id': 480, 'page': 1}, "发改委-广州-规范性文件", "政府文件"),
            ({'id': 482, 'page': 1}, "发改委-广州-工作总结和计划", "年度工作计划及总结"),
            ({'id': 483, 'page': 1}, "发改委-广州-政策解读", "部门解读"),
            ({'id': 485, 'page': 1}, "发改委-广州-人大代表建议和政协提案", "政府文件"),
        ]
        for data, category, classify in urls:
            url = self.base_url.format(**data)
            yield scrapy.Request(url, meta={'category': category, 'classify': classify, 'data': data},
                                 callback=self.parse_ajax, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        next_page = response.xpath('//*[@id="page_div"]/a[@class="next"]/@href').extract_first()
        page_exists = response.xpath('//div[@class="list_li"]//a')
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

    def parse_ajax(self, response: scrapy.http.Response):
        data = response.meta.get('data')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {'category': category, 'classify': classify}
        content = json.loads(response.text)
        total = content.get('total')
        page = data.get('page')
        next_page = page + 1 if total > page * 100 else None
        for item in content.get('articles'):
            url = item.get('url')
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        print('next_page', next_page, meta)
        if next_page:
            data['page'] = next_page
            url = self.base_url.format(**data)
            yield scrapy.Request(url, meta={'category': category, 'classify': classify, 'data': data},
                                 callback=self.parse_ajax, headers=HEADERS)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        if response.xpath('//h1[@class="title"]'):
            item = self.guifan_style(response)
            source_module = '法定主动公开内容-部门文件-{}'.format(category.split('-')[-1])
        else:
            item = self.zhengce_style(response)
            source_module = '-'.join(response.xpath('//div[@class="position mb10"]/a/text()').extract())
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
        index_no = theme = effective_start = effective_end = doc_no = ''
        title = response.xpath('//*[@id="zoomtitl"]/text()').extract_first(default='').strip()
        # source = self.website
        other = response.xpath('string(//*[@id="zoomtime"])').extract_first(default='')
        source = obj_first(re.findall(r'来源：\s*([^\s\|]*)\s*', other))
        publish_time = time_map(other)
        write_time = ''
        content_str = '//*[@id="zoomcon"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str), lower=True).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
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
        item['source'] = source.strip() if source else self.website
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['extension'] = extension
        return item

    def guifan_style(self, response):
        item = PolicyReformItem()
        index_no = theme = exclusive_sub = source = effective_end = doc_no = write_time = publish_time = ''
        title = response.xpath('//h1[@class="title"]/text()').extract_first().strip()
        table = response.xpath('//div[@class="classify"]//tr/td')
        for i in table:
            key = i.xpath('./label/text()').extract_first(default='')
            key = re.sub(r'\s+', '', key)
            value = i.xpath('./span/text()').extract_first(default='').strip()
            if '索引号' in key:
                index_no = value
            elif '成文日期' in key:
                write_time = time_map(value)
            elif '发布日期' in key:
                publish_time = time_map(value)
            elif '文号' in key:
                doc_no = value
            elif '主题词' in key:
                theme = value
            elif '发布机构' in key:
                source = value
            elif '分类' in key:
                exclusive_sub = value

        content_str = '//div[@class="article-content"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
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
