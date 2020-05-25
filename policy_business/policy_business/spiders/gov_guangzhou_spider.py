import datetime
import hashlib
import os
import re
import json
from copy import deepcopy

import scrapy

from policy_business.items import PolicyReformItem, extension_default
from policy_business.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_business.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start

conn = RedisConnect().conn


class GovGuangZhouSpider(scrapy.Spider):
    name = 'GovGuangZhouSpider'

    project_hash = 'policy_business0520'
    website = '广州市人民政府'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.gz.gov.cn/ysgz/tzzc/gjzc/", "国家政策", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/nqzc/", "广州暖企政策", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/bljzxk/", "办理建筑许可", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/djcc/", "登记财产", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/ns/", "纳税", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/kbqy/", "开办企业", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/kjmy/", "跨境贸易", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/hdxd/", "获得信贷", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/hddl/", "获得电力", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/zxht/", "执行合同", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/blpc/", "办理破产", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/bhzxtzz/", "保护中小投资者", "营商环境-广州-营商政策", "政府文件"),
            ("http://www.gz.gov.cn/ysgz/tzzc/zfcg/", "政府采购", "营商环境-广州-营商政策", "政府文件"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, name, category, classify in urls:
            yield scrapy.Request(url, meta={"name": name, 'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        name = response.meta.get('name')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"name": name, 'category': category, 'classify': classify}
        next_page = response.xpath('//*[@id="page_div"]/span/a[@class="next"]/@href').extract_first()
        page_exists = response.xpath('//ul[@class="news_list"]/li//a')
        if not page_exists:
            page_exists = response.xpath('//div[@class="txt"]/a')
        for item in page_exists:
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url)
            if 'htm' not in url:
                pass
                # print(url, response.url)
            else:
                yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        # print('next_page', next_page, meta)
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        # title = response.xpath('//h1[contains(@class,"content_title")]/text()').extract_first()
        if response.xpath('//h1[contains(@class,"content_title")]').extract_first():
            item = self.zhengce_style(response)
        elif response.xpath('//h1[@class="info_title"]/text()'):
            item = self.guifan_style(response)
        else:
            item = self.wenjian_style(response)

        name = response.meta.get('name')
        model_list = response.xpath('//div[@class="curmb"]/a/text()').extract()
        model_list.append(name)
        source_module = '-'.join(model_list)
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
        index_no = theme = effective_start = effective_end = ''
        title = response.xpath('//h1[contains(@class,"content_title")]/text()').extract_first(default='').strip()
        # source = self.website
        source = response.xpath('//*[@id="laiyuan"]/b/text()').extract_first()
        if source:
            source = source.split()[0]
        doc_list = response.xpath(
            '//*[@id="zoomcon"]/*[contains(@align,"center") or contains(@style,"center")]/text()'
            ).extract()
        if not doc_list:
            doc_list = response.xpath(
                '//*[@id="zoomcon"]/*[contains(@align,"center") or contains(@style,"center")]//text()'
            ).extract()
        doc_no = ''.join(doc_list)
        doc_no = re.sub(title, '', doc_no)
        if '号' in doc_no:
            doc_no = obj_first(re.findall(r'(.*?号)', doc_no))

        if len(doc_no) > 20 or not doc_no or not re.findall(r'令|〔.*〕|号', doc_no):
            doc_no = ''
        else:
            doc_no = doc_no.strip()

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
        item['file_type'] = file_type
        item['source'] = source.strip() if source else self.website
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['extension'] = extension
        return item

    def wenjian_style(self, response):
        item = PolicyReformItem()
        index_no = theme = effective_start = publish_time = source = effective_end = doc_no = exclusive_sub = ''
        write_time = ''
        title = response.xpath('//h1[@class="title"]/text()').extract_first().strip()
        table = response.xpath('//div[@class="classify"]//td')
        for i in table:
            key = i.xpath('./label/text()').extract_first(default='')
            doc = re.sub(r'\s+', '', key)
            value = i.xpath('./span/text()').extract_first(default='').strip()
            span = value if value else ''
            if '发布机构' in doc:
                source = span
            elif '文号' in doc:
                doc_no = span
            elif '分类' in doc:
                exclusive_sub = span
            elif '成文日期' in doc:
                write_time = time_map(span)
            elif '主题词' in doc:
                theme = span
            elif '名称' in doc:
                title = span
            elif '索引号' in doc:
                index_no = span
            elif '发布日期' in doc:
                publish_time = time_map(span)

        # source = self.website
        source = source if source else self.website

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
        extension['exclusive_sub'] = exclusive_sub
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
        item = PolicyReformItem()
        index_no = theme = effective_start = source = effective_end = doc_no = ''
        title = response.xpath('//h1[@class="info_title"]/text()').extract_first().strip()
        table = response.xpath('//*[@id="zoomsubtitl"]/ul/li')
        for i in table:
            key = i.xpath('./span/text()').extract_first(default='')
            key = re.sub(r'\s+', '', key)
            value = i.xpath('./text()').extract_first(default='').strip()
            value = value if value else ''
            if '统一编号' in key:
                index_no = value
            elif '实施日期' in key:
                effective_start = time_map(value)
            elif '文号' in key:
                doc_no = value
            elif '失效日期' in key:
                effective_end = time_map(value, error=value)
            elif '发布机关' in key:
                source = value

        # source = self.website
        source = source if source else self.website
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
        if not response.xpath(content_str).extract_first():
            content_str = '//*[@id="info_cont"]'
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
