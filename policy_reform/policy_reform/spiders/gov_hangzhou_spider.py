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


class GovHangZhouSpider(scrapy.Spider):
    name = 'GovHangZhouSpider'

    project_hash = 'pr0414'
    website = '杭州市人民政府'
    # classify = '政府文件'

    data = {
        'infotypeId': 'F0100001',
        'jdid': '149',
        'area': '',
        'divid': 'div1256283',
        'vc_title': '',
        'vc_number': '',
        'sortfield': ',createdatetime:0,orderid:0',
        'currpage': '1',
        'vc_filenumber': '',
        'vc_all': '',
        'texttype': '0',
        'fbtime': '-1',
    }
    headers = HEADERS.copy()
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'http://www.hangzhou.gov.cn/col/col1256283/index.html',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': '__jsluid_h=d500861d9b38e92a8a476c75350b9458; Hm_lvt_d7682ab43891c68a00de46e9ce5b76aa=1568713024; '
                  'Hm_lvt_d457f526f73edcd0b683dc16f64e1f88=1568711131,1568711962,1568712035; _gscu_1342898206=688740'
                  '48xgi6kn19; Hm_lvt_e134fee1edb436d9a4b58261f92fdeb8=1588216193; SERVERID=57526053d080975751a9538d'
                  '16dda0a7|1588731828|1588731727'
    })

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.hangzhou.gov.cn/module/xxgk/search.jsp",
             "", "人民政府-杭州-行政规范性文件", "政府文件"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, source_module, category, classify in urls:
            post_data = self.data.copy()
            yield scrapy.FormRequest(url, formdata=post_data, callback=self.parse, headers=self.headers,
                                     meta={"source_module": source_module, 'category': category, 'classify': classify})

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        next_page = response.xpath(
            '//td[@align="right"]/a[contains(text(), "下一页")]/@href').extract_first()
        next_page = int(obj_first(re.findall(r'\d+', next_page)))
        end_page = response.xpath(
            '//td[@align="right"]/a[contains(text(), "尾 页")]/@href').extract_first()
        end_page = int(obj_first(re.findall(r'\d+', end_page)))
        page_exists = response.xpath('//div//tr/td/a[@gkfs="主动公开"]')
        # if not page_exists:
        #     page_exists = response.xpath('//ul[@class="uli14 pageList "]/li/a')
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
        if next_page <= end_page:
            next_url = 'http://www.hangzhou.gov.cn/module/xxgk/search.jsp'
            post_data = self.data.copy()
            post_data["currpage"] = str(next_page)
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
        title = response.xpath('//tr/td[@class="title"]/text()').extract_first().strip()
        source = response.xpath('//*[@id="c"]/tr[1]/td/table/tr[3]/td[2]/text()').extract_first()
        doc_no = response.xpath('//*[@id="c"]/tr[1]/td/table/tr[2]/td[2]/text()').extract_first()
        publish_time = time_map(response.xpath('//*[@id="c"]/tr[1]/td/table/tr[2]/td[4]/text()').extract_first())
        index_no = response.xpath('//*[@id="c"]/tr[1]/td/table/tr[1]/td[2]/text()').extract_first()
        theme = response.xpath('//*[@id="c"]/tr[1]/td/table/tr[3]/td[4]/text()').extract_first()

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
            extension['file_type'].append('')

        attach_img = response.xpath('{}//img[not(@href="javascript:void(0);")]'.format(content_str))
        img_name = 'alt'
        for a in attach_img:
            file_name = a.xpath('./@{}'.format(img_name)).extract_first()
            url_ = a.xpath('./@src').extract_first()
            if not url_ or url_.split('.')[-1].lower() in IMG_ERROR_TYPE or 'file:/' in url_:
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
