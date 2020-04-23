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
    GovBeiJingPageControl, get_cookie

conn = RedisConnect().conn


class GovGuangDongSpider(scrapy.Spider):
    name = 'GovGuangDongSpider'

    project_hash = 'pr0414'
    website = '广东省人民政府'
    category = '人民政府-广东-{}'
    source_module = '首页-政务公开-文件库-全部文件-{}'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.gd.gov.cn/zwgk/wjk/qbwj/yf/index.html",
             "粤府", "", "政府文件"),
            ("http://www.gd.gov.cn/zwgk/wjk/qbwj/yfb/index.html",
             "粤府办", "", "政府文件"),
            ("http://www.gd.gov.cn/zwgk/wjk/qbwj/ybh/index.html",
             "粤办函", "", "政府文件"),
        ]
        # self.cookies = get_cookie('http://www.gd.gov.cn/zwgk/wjk/qbwj/yf/index.html')
        for url, source_module, _, classify in urls:
            yield scrapy.Request(url,
                                 meta={"source_module": self.source_module.format(source_module),
                                       'category': self.category.format(source_module),
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
                if conn.hget(self.project_hash, source_module + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, source_module + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        # print('next_page', next_page, meta)
        if next_page:
            # next_page = 'http://www.shanghai.gov.cn' + next_page
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        flag1 = response.xpath('string(//div[@class="viewList left"]/div[@class="zw"])').extract_first()  #
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

        # source_module = '-'.join(response.xpath('//ul[@class="breadcrumb"]/li//a/text()').extract())
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
        """2016"""
        item = PolicyReformItem()
        index_no = theme = effective_start = publish_time = source = effective_end = doc_no = ''
        title = write_time = ''
        # title = response.xpath('//div[@class="tit"]/h1/text()').extract_first().strip()
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

        # source = self.website
        source = source if source else self.website
        # publish_time = time_map(response.xpath('//head/meta[@name="PubDate"]/@content').extract_first())

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
        content_str = '//div[@class="article-content"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            if not url_:
                continue
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            extension['file_type'].append('')

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

        # source = self.website
        source = source if source else self.website
        # publish_time = time_map(response.xpath('//head/meta[@name="PubDate"]/@content').extract_first())

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
        content_str = '//div[@class="viewList left"]/div[@class="zw"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            if not url_:
                continue
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            extension['file_type'].append('')

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
