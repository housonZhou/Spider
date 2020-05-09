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
    GovBeiJingPageControl, find_effective_start


class GovBeiJingSpider(scrapy.Spider):
    name = 'GovBeiJingSpider'

    project_hash = 'policy_gov0508'
    website = '北京市人民政府'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.beijing.gov.cn/zhengce/zfwj/zfwj2016/szfl/index.html",
             "人民政府-北京-市政府令", "地方行政规章"),
            ("http://www.beijing.gov.cn/zhengce/gfxwj/index.html",
             "人民政府-北京-规范性文件", "政府文件"),
            ("http://www.beijing.gov.cn/zhengce/dfxfg/index.html",
             "人民政府-北京-地方性法规", "地方行政规章"),
            ("http://www.beijing.gov.cn/zhengce/zcjd/index.html",
             "人民政府-北京-政策解读", "部门解读"),
            ("http://www.beijing.gov.cn/gongkai/guihua/wngh/cqgh/index.html",
             "人民政府-北京-长期规划", "发展规划"),
            ("http://www.beijing.gov.cn/gongkai/guihua/wngh/sjzdzxgh/index.html",
             "人民政府-北京-市级重点专项规划", "专项规划"),
            ("http://www.beijing.gov.cn/gongkai/guihua/wngh/ybzxgh/index.html",
             "人民政府-北京-市级一般专项规划", "专项规划"),
            ("http://www.beijing.gov.cn/gongkai/guihua/wngh/qjghgy/index.html",
             "人民政府-北京-区级规划纲要", "发展规划"),
            ("http://www.beijing.gov.cn/gongkai/guihua/wngh/qtgh/index.html",
             "人民政府-北京-其他规划", "专项规划"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, category, classify in urls:
            yield scrapy.Request(url, meta={"classify": classify, 'category': category},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"classify": classify, 'category': category}
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
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        # print('next_page', next_page, meta)
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.zhengce_style(response)

        source_module = '-'.join(response.xpath('//div[@class="crumbs"]/a/text()').extract())
        classify = response.meta.get('classify')
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        category = response.meta.get('category')
        if (category == '人民政府-北京-地方性法规') and ('人民代表大会' in item.get('title')):
            classify = '地方性法规'
        item['category'] = category
        item['classify'] = classify

        for index, file_name in enumerate(item['extension'].get('file_name')):
            file_url = item['extension'].get('file_url')[index]
            type_ = item['extension'].get('file_type')[index]
            if type_ == 'url':
                continue
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
        tables = response.xpath('//div[@class="container"]/ol/li')
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
                write_time = time_map(span)
            elif '发布日期' in doc:
                publish_time = time_map(span)
            elif '有效性' in doc:
                is_effective = span
            elif '实施日期' in doc:
                effective_start = time_map(span)
            # elif '废止日期' in doc:
            #     effective_end = span
        if pub_other:
            source = '{};{}'.format(source, pub_other)
        if doc_no:
            doc_no = re.sub(r'〔〕号|〔〕', '', doc_no)
        if not doc_no:
            file_type = ''
        elif '〔' in doc_no:
            file_type = obj_first(re.findall('^(.*?)〔', doc_no))
        else:
            file_type = obj_first(re.findall('^(.*?)第', doc_no))
        if not source and not publish_time:
            message = response.xpath('string(//p[@class="fl"])').extract_first(default='')
            source = obj_first(re.findall(r'来源：\s*([^\s\|]*)\s*', message))
            publish_time = time_map(message)

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
            if (not url_) or (download_url == response.url):
                continue
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
        extension['effective_end'] = effective_end
        extension['is_effective'] = effective(effective_start, effective_end) if is_effective == '是' else ''
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
