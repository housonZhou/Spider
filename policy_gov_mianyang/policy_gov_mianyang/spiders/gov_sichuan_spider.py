# coding: utf-8
# Author：houszhou
# Date ：2020/5/13 17:08
# Tool ：PyCharm
import requests
import datetime
import hashlib
import os
import re
import json
from lxml.etree import HTML
from copy import deepcopy

import scrapy

from policy_gov_mianyang.items import PolicyReformItem, extension_default
from policy_gov_mianyang.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE, \
    SCRAPY_TEST, FILE_DOWNLOAD
from policy_gov_mianyang.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, \
    effective, find_effective_start, GovSiChuangPageHTMLControl

conn = RedisConnect().conn


class GovSiChuanSpider(scrapy.Spider):
    name = 'GovSiChuanSpider'

    project_hash = 'policy_gov_mianyang_0527'
    website = '四川省人民政府'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        if RUN_LEVEL != 'FORMAT' and SCRAPY_TEST:
            yield from self.scrapy_test()
        else:
            urls = [
                ("http://www.sc.gov.cn/10462/10464/10684/12419/list_ft.shtml",
                 "", "人民政府-四川-最新文件", "政府文件"),
                ("http://www.sc.gov.cn/10462/10464/10684/10691/stt_list.shtml",
                 "", "人民政府-四川-省政府令", "地方行政规章"),
                ("http://www.sc.gov.cn/10462/10464/10684/10693/zfwj_cff.shtml",
                 "", "人民政府-四川-川府发", "政府文件"),
                ("http://www.sc.gov.cn/10462/10464/10684/10694/zfwj_cfh.shtml",
                 "", "人民政府-四川-川府函", "政府文件"),
                ("http://www.sc.gov.cn/10462/10464/10684/10692/zfwj_cbf.shtml",
                 "", "人民政府-四川-川办发", "政府文件"),
                ("http://www.sc.gov.cn/10462/10464/10684/10695/zfwj_cbh.shtml",
                 "", "人民政府-四川-川办函", "政府文件"),
                ("http://www.sc.gov.cn/10462/10464/10684/13240/stt_list.shtml",
                 "", "人民政府-四川-修订废止", "地方行政规章"),
                ("http://www.sc.gov.cn/10462/10464/13298/13299/zcjd_list.shtml",
                 "", "人民政府-四川-政策解读", "部门解读"),
                ("http://www.sc.gov.cn/10462/10464/13298/14097/bmjd_list.shtml",
                 "", "人民政府-四川-部门解读", "部门解读"),
                ("http://www.sc.gov.cn/10462/10464/13298/13301/bmjd_list.shtml",
                 "", "人民政府-四川-媒体视角", "媒体解读"),
                ("http://www.sc.gov.cn/10462/c101274/sjhbg_list.shtml",
                 "", "人民政府-四川-部门规划计划", "专项规划"),
            ]
            # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
            for url, source_module, category, classify in urls:
                yield scrapy.Request(url, callback=self.parse, headers=HEADERS,
                                     meta={"source_module": source_module, 'category': category, 'classify': classify})

    def scrapy_test(self):
        urls = [
            # ('http://www.sc.gov.cn/10462/10464/13298/13299/2016/7/18/10388550.shtml', '', '', ''),
            ('http://www.sc.gov.cn/zcwj/xxgk/NewT.aspx?i=20200126095645-444864-00-000', '', '', ''),
        ]
        for url, source_module, category, classify in urls:
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS,
                                 meta={"source_module": source_module, 'category': category, 'classify': classify})

    def parse(self, response: scrapy.http.Response):
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        page = GovSiChuangPageHTMLControl(response.text)
        next_page = page.next_page(response.url)
        page_exists = response.xpath('//*[@id="content"]//td//a')
        # if not page_exists:
        #     page_exists = response.xpath('//div[@class="txt"]/a')
        for item in page_exists:
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        print('next_page', next_page, meta)
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        # title = response.xpath('//h1[contains(@class,"content_title")]/text()').extract_first()
        if response.xpath('//td[@class="box"]//td[@class="box"]'):
            item = self.zhengce_style(response)
        else:
            item = self.guifan_style(response)
            # print(item)

        category = response.meta.get('category')
        source_module = response.xpath('//*[@id="container"]/table[2]/tbody/tr/td/text()').extract_first()
        if source_module:
            source_module = re.sub(r' > ', '-', source_module.split('：')[-1]).strip()
        else:
            source_module = '四川省-人民政府-{}'.format(category.split('-')[-1])
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
            file_name = "{}_{}".format(index, file_name)
            item['extension']['file_name'][index] = file_name
            meta = {'row_id': row_id, 'file_name': file_name}
            if FILE_DOWNLOAD:
                yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download,
                                     dont_filter=True)
            else:
                # print(response.url, file_url, meta)
                pass

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        if item["content"]:
            yield item

    def zhengce_style(self, response):
        item = PolicyReformItem()
        effective_start = effective_end = theme = ''
        title = response.xpath('//title/text()').extract_first().split('-')[0].strip()
        # source = self.website
        source = response.xpath('string(//td[@class="box"]//td[@class="box"]/table/tbody/tr[1]/td[6])').extract_first()
        source = source.strip() if source else self.website
        doc_no = response.xpath('string(//td[@class="box"]//td[@class="box"]/table/tbody/tr[2]/td[4])').extract_first()
        if doc_no:
            doc_no = doc_no.strip()
        publish_time = response.xpath('string(//td[@class="box"]//td[@class="box"]/table/tbody/tr[2]/td[2])').extract_first()
        publish_time = time_map(publish_time)
        write_time = ''
        index_no = response.xpath('string(//td[@class="box"]//td[@class="box"]/table/tbody/tr[1]/td[2])').extract_first()
        exclusive_sub = response.xpath('string(//td[@class="box"]//td[@class="box"]/table/tbody/tr[1]/td[4])').extract_first()
        is_eff = response.xpath('string(//td[@class="box"]//td[@class="box"]/table/tbody/tr[2]/td[6])').extract_first()
        is_eff = re.sub(r'\s', '', is_eff) if is_eff else ''

        if not doc_no:
            file_type = ''
        elif '〔' in doc_no:
            file_type = obj_first(re.findall('^(.*?)〔', doc_no))
        elif '[' in doc_no:
            file_type = obj_first(re.findall(r'^(.*?)\[', doc_no))
        elif '第' in doc_no:
            file_type = obj_first(re.findall('^(.*?)第', doc_no))
        elif obj_first(re.findall(r'^(.*?)\d', doc_no)):
            file_type = obj_first(re.findall(r'^(.*?)\d', doc_no))
        else:
            file_type = ''
        content_str = '//td[@valign="top"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = response.urljoin(url_)
            if (not url_) or (download_url == response.url) or re.findall(r'mailto', url_):
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
        if '有效' in is_eff:
            is_effective = effective(effective_start, effective_end)
        elif '失效' in is_eff:
            effective_end = time_map(is_eff)
            is_effective = effective(effective_start, effective_end)
        else:
            is_effective = ''

        extension['doc_no'] = doc_no
        extension['index_no'] = index_no.strip() if index_no else ''
        extension['theme'] = theme.strip() if theme else ''
        extension['exclusive_sub'] = exclusive_sub.strip() if exclusive_sub else ''
        extension['write_time'] = write_time
        extension['effective_start'] = effective_start
        extension['effective_end'] = effective_end
        extension['is_effective'] = is_effective
        item['content'] = content
        item['title'] = title
        item['file_type'] = file_type
        item['source'] = source
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['extension'] = extension
        return item

    def guifan_style(self, response):
        item = PolicyReformItem()
        index_no = theme = effective_start = effective_end = write_time = exclusive_sub = ''
        title = response.xpath('string(//*[@id="articlecontent"]/h2)').extract_first().strip()

        source = response.xpath('//head/meta[@name="ContentSource"]/@content').extract_first()
        source = source.strip() if source else self.website
        publish_time = time_map(response.xpath('//*[@id="articleattribute"]/li[1]/text()').extract_first())
        if not publish_time:
            publish_time = self.get_pub_time(response.url)
        doc_no = response.xpath('//*[@id="cmsArticleContent"]//strong/text()').extract_first()
        if not doc_no:
            doc_no = response.xpath('string(//*[@id="cmsArticleContent"])').extract_first(default='')
            doc_no = re.split(r'\s+', doc_no.strip())[0]
        if (not doc_no) or (not re.findall(r'〔\d+〕|\[\d+\]|【\d+】', doc_no)) or len(doc_no) > 30:
            doc_no = ''
        end = response.xpath('//*[@id="cmsArticleContent"]//font[@color="red"]/text()').extract_first()
        if end and '失效' in end:
            effective_end = time_map(end)

        if not doc_no:
            file_type = ''
        elif '〔' in doc_no:
            file_type = obj_first(re.findall('^(.*?)〔', doc_no))
        elif '[' in doc_no:
            file_type = obj_first(re.findall(r'^(.*?)\[', doc_no))
        elif '【' in doc_no:
            file_type = obj_first(re.findall(r'^(.*?)【', doc_no))
        elif '第' in doc_no:
            file_type = obj_first(re.findall('^(.*?)第', doc_no))
        elif obj_first(re.findall(r'^(.*?)\d', doc_no)):
            file_type = obj_first(re.findall(r'^(.*?)\d', doc_no))
        else:
            file_type = ''
        content_str = '//*[@id="cmsArticleContent"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach = response.xpath('{}//a[not(@href="javascript:void(0);")]'.format(content_str))

        extension = deepcopy(extension_default)
        for a in attach:
            file_name = a.xpath('string(.)').extract_first()
            url_ = a.xpath('./@href').extract_first()
            download_url = response.urljoin(url_)
            if (not url_) or (download_url == response.url) or re.findall(r'mailto', url_):
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
        extension['exclusive_sub'] = exclusive_sub.strip() if exclusive_sub else ''
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

    @staticmethod
    def get_pub_time(response_url):
        try:
            article_id = response_url.split('/')[-1].split('.')[0]
            url = "http://www.sc.gov.cn/wechat/ArticleDateTime/GetArticleDateTime.aspx?articleId={}" \
                  "&marginTop=3&bgColor=e7e7e7".format(article_id)
            resp = requests.get(url, headers=HEADERS)
            content = resp.text
            tree = HTML(content)
            return time_map(obj_first(tree.xpath('//*[@id="d"]/text()')))
        except Exception as e:
            print('get_pub_time error:　{}'.format(e))
            return ''

