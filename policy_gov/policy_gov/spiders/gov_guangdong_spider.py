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
    find_effective_start, format_file_type, format_doc_no

conn = RedisConnect().conn


class GovGuangDongSpider(scrapy.Spider):
    name = 'GovGuangDongSpider'

    project_hash = 'policy_gov0508'
    website = '广东省人民政府'
    category = '人民政府-广东-{}'
    zhengce_module = '首页-政务公开-文件库-全部文件-{}'
    jiedu_model = '首页-政务公开-政策解读-省内政策-{}'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.gd.gov.cn/zwgk/wjk/qbwj/yfl/index.html", self.zhengce_module,
             "粤府令", "地方行政规章"),
            ("http://www.gd.gov.cn/zwgk/wjk/qbwj/yfh/index.html", self.zhengce_module,
             "粤府函", "政府文件"),
            ("http://www.gd.gov.cn/zwgk/jhgh/index.html", self.jiedu_model,
             "计划规划", "专项规划"),
            ("http://www.gd.gov.cn/zwgk/zcjd/bmjd/index.html", self.jiedu_model,
             "部门解读", "部门解读"),
            ("http://www.gd.gov.cn/zwgk/zcjd/mtjd/index.html", self.jiedu_model,
             "媒体解读", "媒体解读"),
            ("http://www.gd.gov.cn/zwgk/zcjd/gnzcsd/index.html", self.jiedu_model,
             "国内政策", "媒体解读"),
            ("http://www.gd.gov.cn/zwgk/zcjd/snzcsd/index.html", self.jiedu_model,
             "省内政策", "媒体解读"),
            ("http://www.gd.gov.cn/zwgk/zcjd/wjjd/index.html", self.jiedu_model,
             "一图读懂", "部门解读"),
        ]
        # self.cookies = get_cookie('http://www.gd.gov.cn/zwgk/wjk/qbwj/yf/index.html')
        for url, source_module, category, classify in urls:
            yield scrapy.Request(url,
                                 meta={"source_module": source_module.format(category),
                                       'category': self.category.format(category),
                                       'classify': classify},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        next_page = response.xpath('//div[@class="page"]/a[@class="next"]/@href').extract_first()
        page_exists = response.xpath('//div[@class="viewList"]/ul/li/span/a')
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
            print(next_page)
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        flag1 = response.xpath('string(//div[contains(@class, "iewList")]/div[@class="zw"])').extract_first()  #
        flag2 = response.xpath('string(//div[@class="article-content"])').extract_first()
        if flag1:
            item = self.guifan_style(response)
        elif flag2:
            item = self.zhengce_style(response)
        else:
            meta = {"source_module": source_module, 'category': category, 'classify': classify}
            post_id = int(re.findall(r'post_(\d+)\.html', response.url)[0])
            real_url = 'http://www.gd.gov.cn/gkmlpt/content/{}/{}/post_{}.html'.format(int(post_id / 1000000),
                                                                                       int(post_id / 1000),
                                                                                       post_id)
            return scrapy.Request(real_url, callback=self.parse_detail, headers=HEADERS, meta=meta)
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
        """2016"""
        item = PolicyReformItem()
        index_no = theme = effective_start = publish_time = source = effective_end = doc_no = ''
        title = write_time = ''
        table = response.xpath('//div[@class="classify"]//td')
        for i in table:
            key = i.xpath('./label/text()').extract_first()
            key = re.sub(r'\s+', '', key) if key else ''
            value = i.xpath('./span/text()').extract_first()
            value = value.strip() if value else ''
            if '索引号' in key:
                index_no = value
            elif '主题词' in key:
                theme = value
            elif '文号' in key:
                doc_no = value
            elif '发布日期' in key:
                publish_time = time_map(value, error=value)
            elif '发布机构' in key:
                source = value
            elif '成文日期' in key:
                write_time = value
            elif '名称' in key:
                title = value
        source = source if source else self.website
        content_str = '//div[@class="article-content"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first(default='').strip()
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
        img_name = 'none'
        for a in attach_img:
            file_name = a.xpath('./@{}'.format(img_name)).extract_first(default='').strip()
            url_ = a.xpath('./@src').extract_first()
            if not url_ or url_.split('.')[-1].lower() in IMG_ERROR_TYPE:
                continue
            if not file_name:
                file_name = url_.split('/')[-1]
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            extension['file_type'].append('')
            # print(file_name, download_url)
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
        item['source'] = source
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['extension'] = extension
        return item

    def guifan_style(self, response):
        """2019年"""
        item = PolicyReformItem()
        index_no = theme = effective_start = publish_time = source = effective_end = doc_no = ''
        title = write_time = ''
        # title = response.xpath('//div[@class="tit"]/h1/text()').extract_first().strip()
        table = response.xpath('//div[@class="introduce"]/div/div')
        for i in table:
            key = i.xpath('./label/text()').extract_first()
            key = re.sub(r'\s+', '', key) if key else ''
            value = i.xpath('./span/text()').extract_first()
            value = value.strip() if value else ''
            if '索引号' in key:
                index_no = value
            elif '分类' in key:
                theme = value
            elif '文号' in key:
                doc_no = value
            elif '发布日期' in key:
                publish_time = time_map(value, error=value)
            elif '发布机构' in key:
                source = value
            elif '成文日期' in key:
                write_time = value
            elif '标题' in key:
                title = value
        if not table:
            title = response.xpath('string(//*[@class="zw-title"])').extract_first(default='').strip()
            other = response.xpath('string(//*[@class="zw-info"])').extract_first(default='').strip()
            source = obj_first(re.findall(r'来源 : (\S*)', other))
            publish_time = time_map(other)

        source = source if source else self.website
        content_str = '//div[contains(@class, "viewList")]/div[@class="zw"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))
        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first(default='').strip()
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
        img_name = 'none'
        for a in attach_img:
            file_name = a.xpath('./@{}'.format(img_name)).extract_first(default='').strip()
            url_ = a.xpath('./@src').extract_first()
            if not url_ or url_.split('.')[-1].lower() in IMG_ERROR_TYPE:
                continue
            if not file_name:
                file_name = url_.split('/')[-1]
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            extension['file_type'].append('')
            # print(file_name, download_url)
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
        item['source'] = source
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
