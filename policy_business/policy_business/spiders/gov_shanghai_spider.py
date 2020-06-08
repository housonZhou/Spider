import datetime
import hashlib
import json
import os
import re
from copy import deepcopy

import scrapy

from policy_business.items import PolicyReformItem, extension_default
from policy_business.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_business.util import obj_first, RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start, format_doc_no, format_file_type


class GovShangHaiSpider(scrapy.Spider):
    name = 'GovShangHaiSpider'

    project_hash = 'policy_business0520'
    website = '上海市人民政府'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)
    file_dir = r'C:\Users\17337\houszhou\data\SpiderData\发改营商环境\附件\上海市人民政府\{}'.format(today)
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)

    def start_requests(self):
        urls = [
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw43679/index.html",
             "开办企业", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw43696/index.html",
             "施工许可", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw43680/index.html",
             "获得电力", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw43698/index.html",
             "财产登记", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw43681/index.html",
             "跨境贸易", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw43699/index.html",
             "纳税", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw43700/index.html",
             "获得信贷", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw44854/index.html",
             "执行合同", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw48647/index.html",
             "办理破产", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw48649/index.html",
             "政府采购", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43674/nw48896/index.html",
             "投资指南", "营商环境-上海-政策集锦", "政府文件"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43676/nw43687/index.html",
             "开办企业", "营商环境-上海-政策解读", "部门解读"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43676/nw43688/index.html",
             "施工许可", "营商环境-上海-政策解读", "部门解读"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43676/nw43702/index.html",
             "获得电力", "营商环境-上海-政策解读", "部门解读"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43676/nw43689/index.html",
             "财产登记", "营商环境-上海-政策解读", "部门解读"),
            ("http://www.shanghai.gov.cn/nw2/nw2314/nw43190/nw43672/nw43676/nw43690/index.html",
             "纳税", "营商环境-上海-政策解读", "部门解读"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, name, category, classify in urls:
            yield scrapy.Request(url, meta={"name": name, 'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        name = response.meta.get('name')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"name": name, 'category': category, 'classify': classify}
        next_page = response.xpath(
            '//ul[@class="pagination"]//a[@class="next" or @class="action"]/@href').extract_first()
        page_exists = response.xpath('//div[@class="article-details"]//a')
        if not page_exists:
            page_exists = response.xpath('//ul[@class="uli14 nowrapli border"]//a')
        for item in page_exists:
            link = item.xpath('./@href').extract_first()
            url = response.urljoin(link)
            url_title = item.xpath('./text()').extract_first()
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            if 'htm' in url:
                print('html_url', url)
                yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
            # else:
            #     file_meta = meta.copy()
            #     file_meta.update({'title': url_title})
            #     yield scrapy.Request(url, callback=self.parse_file, headers=HEADERS, meta=file_meta)
        print('next_page', next_page, meta)
        if next_page:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_file(self, response: scrapy.http.Response):
        file_io = response.body
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        title = response.meta.get('title')
        file_name = response.url.split('/')[-1]
        save_dir = os.path.join(self.file_dir, row_id)
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        file_path = os.path.join(save_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(file_io)
        print('文件下载成功： ', file_path)
        item = PolicyReformItem()
        extension = deepcopy(extension_default)
        source_module = response.meta.get('name')
        # item['content'] = ''
        item['title'] = title
        # item['file_type'] = ''
        # item['source'] = ''
        # item['publish_time'] = ''
        # item['html_content'] = ''
        item['extension'] = json.dumps(extension, ensure_ascii=False)
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        item['classify'] = response.meta.get('classify')
        item['category'] = response.meta.get('category')
        print(item)
        return item

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.zhengce_style(response)

        source_module = '-'.join(response.xpath('//ul[@class="breadcrumb"]/li//a/text()').extract())
        doc_no = item['extension']['doc_no']
        doc_no = format_doc_no(doc_no)
        item['extension']['doc_no'] = doc_no
        item['file_type'] = format_file_type(doc_no)
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module if source_module else response.meta.get('name')
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
            file_name = '{}_{}'.format(index, file_name)  # 加上索引，防止重复
            item['extension']['file_name'][index] = file_name
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
        content_str = '//*[@id="ivs_content"]'
        if not response.xpath(content_str):
            content_str = '//div[@class="Article_content"]'
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
