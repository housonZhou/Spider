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
    find_effective_start


class GovShangHaiSpider(scrapy.Spider):
    name = 'GovShangHaiSpider'

    project_hash = 'policy_gov0508'
    website = '上海市人民政府'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw41893/index.html",
             "", "人民政府-上海-政策解读", "部门解读"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw39197/index.html",
             "", "人民政府-上海-修订废止", "地方行政规章"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw44142/index.html",
             "", "人民政府-上海-党政混合信息", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw22396/nw39378/index.html",
             "", "人民政府-上海-上海市国民经济和社会发展第十三个五年规划纲要", "发展规划"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw22396/nw22401/index.html",
             "", "人民政府-上海-上海市国民经济和社会发展第十二个五年规划纲要", "发展规划"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw22396/nw22399/index.html",
             "", "人民政府-上海-年度重点工作", "专项规划"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw22396/nw22400/index.html",
             "", "人民政府-上海-上海市经济和社会发展计划", "专项规划"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw22396/nw22403/index.html",
             "", "人民政府-上海-专项规划", "专项规划"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, source_module, category, classify in urls:
            yield scrapy.Request(url, meta={"source_module": source_module, 'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"source_module": source_module, 'category': category, 'classify': classify}
        next_page = response.xpath(
            '//div[@class="pagination pagination-centered"]//a[@class="action"]/@href').extract_first()
        page_exists = response.xpath('//ul[@class="uli14 pageList"]/li/a')
        if not page_exists:
            page_exists = response.xpath('//ul[@class="uli14 pageList "]/li/a')
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
            next_page = 'http://www.shanghai.gov.cn' + next_page
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.zhengce_style(response)

        source_module = '-'.join(response.xpath('//ul[@class="breadcrumb"]/li//a/text()').extract())
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
            file_type = os.path.splitext(file_url.split('/')[-1])[-1]  # 链接的文件类型
            file_name_type = os.path.splitext(file_name)[-1]  # 页面上显示的文件类型
            if (not file_name_type) or re.findall(r'[^\.a-zA-Z0-9]', file_name_type) or len(file_name_type) > 7:
                file_name = file_name + file_type
            meta = {'row_id': row_id, 'file_name': file_name}
            if RUN_LEVEL == 'FORMAT':
                yield scrapy.Request(file_url, meta=meta, headers=HEADERS, callback=self.file_download, dont_filter=True)
            else:
                print(response.url, file_url, meta)

        item['extension'] = json.dumps(item['extension'], ensure_ascii=False)
        if PRINT_ITEM:
            print(item)
        yield item

    def zhengce_style(self, response):
        item = PolicyReformItem()
        index_no = theme = effective_start = is_effective = effective_end = ''
        title = response.xpath('//*[@id="ivs_title"]/text()').extract_first().strip()
        source = self.website
        doc_no = response.xpath('//*[@id="ivs_content"]/p[@style="text-align: center;"]/text()').extract_first()
        doc_no = doc_no.strip() if doc_no else ''
        time_xpath = response.xpath('string(//h2[@class="no-margin-top"])').extract_first().replace('\n', ' ')
        publish_time = time_map(obj_first(re.findall(r'发布日期：(\S+)', time_xpath)))
        write_time = time_map(obj_first(re.findall(r'印发日期：(\S+)', time_xpath)))
        if not publish_time and not write_time:
            publish_time = time_map(response.xpath('string(//*[@id="ivs_date"])').extract_first())

        if not doc_no or re.findall(r'批准|通过', doc_no):
            doc_no = ''
            file_type = ''
        elif '〔' in doc_no:
            file_type = obj_first(re.findall('^(.*?)〔', doc_no))
        elif '第' in doc_no:
            file_type = obj_first(re.findall('^(.*?)第', doc_no))
        elif obj_first(re.findall(r'^(.*?)\d', doc_no)):
            file_type = obj_first(re.findall(r'^(.*?)\d', doc_no))
        else:
            file_type = ''
        content_str = '//*[@id="ivs_content"]'
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
