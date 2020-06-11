import datetime
import hashlib
import os
import re
import json
import time
from copy import deepcopy

import scrapy

from policy_gov.items import PolicyReformItem, extension_default
from policy_gov.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_gov.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start, format_file_type, format_doc_no

conn = RedisConnect().conn


class GovSpider(scrapy.Spider):
    name = 'GovSpider'

    project_hash = 'policy_gov0508'
    website = '国务院'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://sousuo.gov.cn/column/30471/0.htm", "首页-政策-中央有关文件", "人民政府-国家-中央有关文件", "政策"),
            ("http://sousuo.gov.cn/column/30474/0.htm", "首页-政策-解读", "人民政府-国家-部门", "部门解读"),
            ("http://sousuo.gov.cn/column/30469/0.htm", "国家-首页-最新", "人民政府-国家-中央政府文件", "政府文件"),
            ("http://sousuo.gov.cn/column/30593/0.htm", "国家-首页-专家", "人民政府-国家-专家", "专家解读"),
            ("http://sousuo.gov.cn/column/40048/0.htm", "国家-首页-媒体", "人民政府-国家-媒体", "媒体解读"),
            ("http://sousuo.gov.cn/column/30214/0.htm", "国家-首页-白皮书", "人民政府-国家-白皮书", "政府白皮书"),
        ]
        for url, source_module, category, classify in urls:
            yield scrapy.Request(url, meta={"source_module": source_module, 'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)

        urls = [
            ("http://sousuo.gov.cn/list.htm?q=&n=15&p=0&t=paper&sort=publishDate&childtype=&subchildtype=&pcodeJiguan=&"
             "pcodeYear=&pcodeNum=&location=&searchfield=title&title=&content=&pcode=&puborg=&timetype=timeqb&mintime=&"
             "maxtime=", "首页-政策-解读", "人民政府-国家-信息公开", "政府文件")]
        for url, source_module, category, classify in urls:
            yield scrapy.Request(url, meta={"source_module": source_module, 'category': category, 'classify': classify},
                                 callback=self.parse_msg, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        source_module = response.meta.get('source_module')
        category = response.meta.get('category')
        classify = response.meta.get('classify')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        next_page = response.xpath('//div[@class="newspage cl"]/ul/li/a[@class="next"]/@href').extract_first()

        for item in response.xpath('//ul[@class="listTxt"]/li/h4/a'):
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            if url in ('http://www.gov.cn/zhengce/qiyefugongfuchanzczlc/index.htm',
                       'http://www.gov.cn/zhengce/jyyjc/index.htm'):
                continue
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # conn.hset(self.project_hash, category + '-' + url, 1)  # 直接设置，不去重
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)

        if next_page:
            print(next_page, meta)
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_msg(self, response: scrapy.http.Response):
        """信息公开"""
        source_module = response.meta.get('source_module')
        category = response.meta.get('category')
        classify = response.meta.get('classify')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        next_page = response.xpath(
            '//div[@class="pageInfo"]/span[@class="wcm_pointer nav_go_next"]/a/@href').extract_first()
        for item in response.xpath('//div[@class="dataBox"]//td[@class="info"]/a'):
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            if url in ('http://www.gov.cn/zhengce/qiyefugongfuchanzczlc/index.htm',
                       'http://www.gov.cn/zhengce/jyyjc/index.htm'):
                continue
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # conn.hset(self.project_hash, category + '-' + url, 1)  # 直接设置，不去重
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)

        if next_page:
            print(next_page, meta)
            time.sleep(1.5)
            yield scrapy.Request(next_page, callback=self.parse_msg, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        if response.xpath('//div[@class="article oneColumn pub_border"]/h1') or response.xpath(
                '//div[@class="pages-title"]/text()'):
            item = self.news_style(response)
        else:
            item = self.zhengce_style(response)
        doc_no = item['extension'].get('doc_no', '')
        doc_no = format_doc_no(doc_no)
        item['extension']['doc_no'] = doc_no
        item['file_type'] = format_file_type(doc_no)
        category = response.meta.get('category')
        classify = response.meta.get('classify')
        if category == '人民政府-国家-中央有关文件':
            item['source'] = self.match_source(item['title'])
        elif (category == '人民政府-国家-信息公开') and (item["file_type"] == '国令'):
            classify = '行政法规'
        source_module = '-'.join(response.xpath('//div[@class="BreadcrumbNav"]//a/text()').extract())
        if not source_module:
            source_module = '-'.join(response.xpath('//div[@class="crumbs"]//a/text()').extract())
        # item = PolicyReformItem()
        # item['content'] = content
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
                pass
                # print(response.url, file_url, meta)

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        if item["content"]:
            yield item
        else:
            print('not content:{}'.format(response.url))

    def news_style(self, response):
        item = PolicyReformItem()
        effective_start = effective_end = ''
        title = response.xpath('string(//div[@class="article oneColumn pub_border"]/h1)').extract_first()
        if not title:
            title = response.xpath('string(//div[@class="pages-title"]/text())').extract_first().strip()
        else:
            title = title.strip()
        content_str = '//*[@id="UCAP-CONTENT"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()
        html_content = get_html_content(response, content_str).strip()
        other = response.xpath('string(//div[@class="pages-date"])').extract_first()
        publish_time = time_map(other)
        source = obj_first(re.findall(r'来源：\s*(\S*)', other))
        source = source if source else self.website
        extension = deepcopy(extension_default)
        attach_str = '{}//a[not(@href="javascript:void(0);")]'
        attach = response.xpath('{}|{}'.format(attach_str.format(content_str),
                                               attach_str.format('//div[@class="xg-list related"]')))
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
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
        extension['effective_start'] = effective_start
        extension['is_effective'] = effective(effective_start, effective_end)
        extension['effective_end'] = effective_end
        extension['theme'] = ''
        extension['exclusive_sub'] = ''
        extension['doc_no'] = ''
        item['content'] = content
        item['title'] = title
        item['source'] = source
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['extension'] = extension
        return item

    def zhengce_style(self, response):
        item = PolicyReformItem()
        table = response.xpath('//div[@class="wrap"]/table[1]//tr/td/b')
        index_no = write_time = title = doc_no = publish_time = theme = source = effective_end = effective_start = ''
        exclusive_sub = ''
        for i in table:
            key = i.xpath('./text()').extract_first()
            key = re.sub(r'\s+', '', key)
            value = i.xpath('../following-sibling::td[1]/text()').extract_first()
            value = value if value else ''
            if '索引号' in key:
                index_no = value
            elif '成文日期' in key:
                write_time = time_map(value)
            elif '标题' in key:
                title = value
            elif '发文字号' in key:
                doc_no = value
            elif '发布日期' in key:
                publish_time = time_map(value)
            elif '主题词' in key:
                theme = value
            elif '发文机关' in key:
                source = value
            elif '主题分类' in key:
                exclusive_sub = value
        content_str_sort = '//div[@class="wrap"]/table[2]/tbody/tr/td[1]/table[1]/tbody/tr/td/table[1]'
        content_str_long = '//div[@class="wrap"]/table[2]//tr/td[1]/table[1]'
        if response.xpath('string({})'.format(content_str_sort)).extract_first():
            content_str = content_str_sort
        else:
            content_str = content_str_long
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()
        html_content = get_html_content(response, content_str).strip()
        extension = deepcopy(extension_default)
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            if not url_:
                continue
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            if re.findall(r'htm', url_):
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

        extension = deepcopy(extension_default)
        extension['doc_no'] = doc_no
        extension['index_no'] = index_no
        extension['theme'] = theme
        extension['exclusive_sub'] = exclusive_sub
        extension['write_time'] = write_time
        extension['effective_start'] = effective_start
        extension['effective_end'] = effective_end
        extension['is_effective'] = effective(effective_start, '')
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

    @staticmethod
    def match_source(title):
        source = '中共中央'
        match_word = re.findall(r'中共中央办公厅|国务院办公厅|中共中央|国务院', title)
        return ';'.join(set(match_word)) if match_word else source
