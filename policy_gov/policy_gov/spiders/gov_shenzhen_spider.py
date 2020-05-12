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
    GovBeiJingPageControl, find_effective_start

conn = RedisConnect().conn


class GovShenZhenSpider(scrapy.Spider):
    name = 'GovShenZhenSpider'

    project_hash = 'policy_gov0508'
    website = '深圳市人民政府'
    # category = '人民政府-深圳-{}'
    # source_module = '首页-政务公开-政府信息公开-政府文件-{}'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.sz.gov.cn/zwgk/zfxxgk/zfwj/szfl/index.html",
             "人民政府-深圳-市政府令", "地方行政规章"),
            ("http://www.sz.gov.cn/cn/xxgk/zfxxgj/zcfg/szsfg/index.html",
             "人民政府-深圳-深圳市法规及规章", "政府文件"),
            ("http://www.sz.gov.cn/cn/xxgk/zfxxgj/ghjh/csgh/zt/index.html",
             "人民政府-深圳-总体规划", "专项规划"),
            ("http://www.sz.gov.cn/cn/xxgk/zfxxgj/ghjh/csgh/zxgh/index.html",
             "人民政府-深圳-专项规划", "专项规划"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, category, classify in urls:
            yield scrapy.Request(url, meta={'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)
        # urls = [
        #     ("http://search.gd.gov.cn/jsonp/site/755001?callback=jQuery191039059891120008783_1589195230131&order=1&"
        #      "category_id=2279&page=1&including_url_doc=1&pagesize=10&"
        #      "json_ext_filter=%7B%22EXT_jdfs%22%3A%22%E6%96%87%E5%AD%97%22%7D&_=1589195230133",
        #      "人民政府-深圳-文字解读", "部门解读"),
        #     ("http://search.gd.gov.cn/jsonp/site/755001?callback=jQuery19104782807608425055_1589195799225&order=1&"
        #      "category_id=2279&page=1&including_url_doc=1&pagesize=10&"
        #      "json_ext_filter=%7B%22EXT_jdfs%22%3A%22%E5%9B%BE%E8%A1%A8%E5%9B%BE%E8%A7%A3%22%7D&_=1589195799230",
        #      "人民政府-深圳-图解政策", "部门解读"),
        # ]
        # for url, category, classify in urls:
        #     yield scrapy.Request(url, meta={'category': category, 'classify': classify},
        #                          callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        next_page = response.xpath('//div[@class="rightcon"]/a[@class="next"]/@href').extract_first()
        page_exists = response.xpath('//div[@class="zx_ml_list"]//li//a')
        for item in page_exists:
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            time.sleep(.5)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        # print('next_page', next_page, meta)
        if next_page:
            time.sleep(.5)
            # next_page = 'http://www.shanghai.gov.cn' + next_page
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        time.sleep(.5)
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.guifan_style(response)

        source_module = '-'.join(response.xpath('//div[@class="zx_rm_tit"]//a/text()').extract())
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
            if not file_name:
                file_name = file_url.split('/')[-1]
            file_type = os.path.splitext(file_url.split('/')[-1])[-1]
            file_name_type = os.path.splitext(file_name)[-1]
            if (not file_name_type) or re.findall(r'[^\.a-zA-Z0-9]', file_name_type) or len(file_name_type) > 7:
                file_name = file_name + file_type
            meta = {'row_id': row_id, 'file_name': file_name}
            if RUN_LEVEL == 'FORMAT':
                yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download,
                                     dont_filter=True)
            else:
                print(response.url, file_url, meta)

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        yield item

    def zhengce_style(self, response):
        item = PolicyReformItem()
        index_no = theme = effective_start = is_effective = effective_end = ''
        title = response.xpath('//div[@class="tit"]/h1/text()').extract_first().strip()
        # source = self.website
        source = response.xpath('//*[@id="laiyuan"]/b/text()').extract_first()
        if source:
            source = source.split()[0]
        doc_no = response.xpath('//*[@id="zoomcon"]/p[1]/text()').extract_first()
        if not doc_no:
            doc_no = response.xpath('//*[@id="zoomcon"]/p[2]/text()').extract_first()
        doc_no = doc_no.strip() if doc_no else ''
        publish_time = time_map(response.xpath('//head/meta[@name="PubDate"]/@content').extract_first())
        write_time = ''

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
        content_str = '//*[@id="zoomcon"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
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

    def guifan_style(self, response):
        item = PolicyReformItem()
        index_no = theme = effective_start = publish_time = source = effective_end = doc_no = ''
        title = response.xpath('//div[@class="tit"]/h1/text()').extract_first().strip()
        table = response.xpath('//div[@class="xx_con"]/p')
        for i in table:
            key = i.xpath('./em/text()').extract_first()
            key = re.sub(r'\s+', '', key) if key else ''
            value = i.xpath('./text()').extract_first()
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
        if not source:
            source = obj_first(
                re.findall(r'来源：(\S+)', response.xpath('//div[@class="tit"]/h6/span[1]/text()').extract_first())
            )
        source = source if source else self.website
        if not publish_time:
            publish_time = time_map(response.xpath('//div[@class="tit"]/h6/span[2]/text()').extract_first())
        write_time = ''

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
        content_str = '//div[@class="news_cont_d_wrap"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format('//div[@class="fjdown"]'))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            if not url_:
                continue
            download_url = response.urljoin(url_)
            extension['file_name'].append(file_name.strip())
            extension['file_url'].append(download_url)
            if re.findall(r'htm', url_):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')

        attach_img = response.xpath('{}//img[not(@href="javascript:void(0);")]'.format('//div[@class="fjdown"]'))
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
        extension['is_effective'] = effective(effective_start, effective_end)
        extension['effective_end'] = effective_end
        item['content'] = content
        item['title'] = title
        item['file_type'] = file_type
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
