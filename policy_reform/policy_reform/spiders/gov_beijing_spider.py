import datetime
import hashlib
import os
import re
import json
from copy import deepcopy

import scrapy

from policy_reform.items import PolicyReformItem, extension_default
from policy_reform.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM
from policy_reform.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    GovBeiJingPageControl


class GovBeiJingSpider(scrapy.Spider):
    name = 'GovBeiJingSpider'

    project_hash = 'pr0414'
    website = '北京市人民政府'
    classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.beijing.gov.cn/zhengce/zhengcefagui/index.html",
             "政务公开-政策公开-政策文件", "人民政府-北京-政策文件"),
            ("http://www.beijing.gov.cn/zhengce/zfwj/zfwj2016/szfwj/index.html",
             "政务公开-政策公开-政策文件-2016年以后政府文件-市政府文件", "人民政府-北京-政府文件"),
            ("http://www.beijing.gov.cn/zhengce/zfwj/zfwj2016/bgtwj/index.html",
             "政务公开-政策公开-政策文件-2016年以后政府文件-市政府文件", "人民政府-北京-市政府办公厅文件"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, source_module, category in urls:
            yield scrapy.Request(url, meta={"source_module": source_module, 'category': category},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        source_module = response.meta.get('source_module')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category}
        url = response.url
        if '/zfwj2016/' in url:
            pager = JsPage(response.text)
        else:
            pager = GovBeiJingPageControl(response.text)
        next_page = pager.next_page(url)

        for item in response.xpath('//ul[@class="list"]/li/a'):
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
        item = self.zhengce_style(response)

        # source_module = '-'.join(response.xpath('//div[@class="BreadcrumbNav"]/a/text()').extract())
        source_module = response.meta.get('source_module')
        # item = PolicyReformItem()
        # item['content'] = content
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        # item['title'] = title
        # item['file_type'] = file_type
        item['classify'] = self.classify
        # item['source'] = source
        item['category'] = response.meta.get('category')
        # item['publish_time'] = publish_time
        # item['html_content'] = html_content
        for index, file_name in enumerate(item['extension'].get('file_name')):
            file_url = item['extension'].get('file_url')[index]
            file_type = os.path.splitext(file_url.split('/')[-1])[-1]
            file_name_type = os.path.splitext(file_name)[-1]
            if (not file_name_type) or re.findall(r'[^\.a-zA-Z0-9]', file_name_type) or len(file_name_type) > 7:
                file_name = file_name + file_type
            meta = {'row_id': row_id, 'file_name': file_name}
            yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download, dont_filter=True)

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        yield item

    def zhengce_style(self, response):
        item = PolicyReformItem()
        index_no = write_time = doc_no = publish_time = theme = ''
        source = pub_other = effective_start = is_effective = effective_end = ''
        title = response.xpath('//div[@class="header"]//p/text()').extract_first().strip()
        tables = response.xpath('//ol/li')
        for i in tables:
            doc = i.xpath('./text()').extract_first()
            span = ''.join(i.xpath('string(./span)').extract())
            span = span if span else ''
            if '发文机构' in doc:
                source = span
            elif '联合发文单位' in doc:
                pub_other = span
            elif '发文字号' in doc:
                doc_no = span
            elif '主题分类' in doc:
                theme = span
            elif '成文日期' in doc:
                write_time = span
            elif '发布日期' in doc:
                publish_time = span
            elif '有效性' in doc:
                is_effective = span
            elif '实施日期' in doc:
                effective_start = span
            # elif '废止日期' in doc:
            #     effective_end = span
        if pub_other:
            source = '{};{}'.format(source, pub_other)
        if not doc_no:
            file_type = ''
        elif '〔' in doc_no:
            file_type = obj_first(re.findall('^(.*?)〔', doc_no))
        else:
            file_type = obj_first(re.findall('^(.*?)第', doc_no))

        content_str = '//*[@id="mainText"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('//ul[@class="fujian"]/li/a[not(@href="javascript:void(0);")]')

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            extension['file_type'].append('')

        extension['doc_no'] = doc_no
        extension['index_no'] = index_no
        extension['theme'] = theme
        extension['write_time'] = write_time
        extension['effective_start'] = effective_start
        extension['effective_end'] = effective_end
        extension['is_effective'] = '先行有效' if is_effective == '是' else ''
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


class JsPage:
    """
    <script type="text/javascript">
    var pageName = "index";
    var pageExt = "html";
    var pageIndex = 1 + 1;
    var pageCount = 11;
    """

    def __init__(self, response):
        try:
            self.find = True
            self.total = int(re.findall(r'var pageCount \= (\d+);', response)[0])
            self.now = int(re.findall(r'var pageIndex \= (\d+) \+ 1', response)[0])
            self.default = re.findall(r'var pageName \= "(.*?)";', response)[0]
            self.type = re.findall(r'var pageExt \= "(.*?)";', response)[0]
        except:
            self.find = self.total = self.now = self.default = self.type = None

    def next_page(self, url):
        if not self.find:
            return None
        elif self.total - 1 > self.now:
            base_url = url.split('/')
            base_url[-1] = '{}_{}.{}'.format(self.default, self.now + 1, self.type)
            return '/'.join(base_url)
        else:
            return None
