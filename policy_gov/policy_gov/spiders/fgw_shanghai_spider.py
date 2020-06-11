# coding: utf-8
# Author：houszhou
# Date ：2020/6/9 16:53
# Tool ：PyCharm
import datetime
import hashlib
import json
import os
import re
from copy import deepcopy

import scrapy

from policy_gov.items import PolicyReformItem, extension_default
from policy_gov.settings import HEADERS, FILES_STORE, RUN_LEVEL, PRINT_ITEM, IMG_ERROR_TYPE
from policy_gov.util import RedisConnect, xpath_from_remove, time_map, get_html_content, effective, \
    find_effective_start, format_file_type, format_doc_no


class FgwShangHaiSpider(scrapy.Spider):
    name = 'FgwShangHaiSpider'

    project_hash = 'policy_gov0508'
    website = '上海市发展和改革委员会'
    # classify = '政府文件'

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://fgw.sh.gov.cn/ggjd/index.html", "发改委-上海-规划解读", "部门解读"),
            ("http://fgw.sh.gov.cn/ggwbhwgwj/index.html", "发改委-上海-规划文本和有关文件", "发展规划"),
            ("http://fgw.sh.gov.cn/jgl/", "发改委-上海-价格类政策文件", "政府文件"),
            ("http://fgw.sh.gov.cn/zcwj01/index.html", "发改委-上海-能源管理和节能减排政策文件", "政府文件"),
            ("http://fgw.sh.gov.cn/zcwj02/", "发改委-上海-产业发展政策文件", "政府文件"),
            ("http://fgw.sh.gov.cn/bwyfz/index.html", "发改委-上海-服务业发展", "政府文件"),
            ("http://fgw.sh.gov.cn/cxfz/index.html", "发改委-上海-创新发展", "政府文件"),
            ("http://fgw.sh.gov.cn/gyfz/index.html", "发改委-上海-区域发展", "政府文件"),
            ("http://fgw.sh.gov.cn/cxzx/", "发改委-上海-创新中心", "政府文件"),
            ("http://fgw.sh.gov.cn/dzbzgg/index.html", "发改委-上海-投资体制改革", "政府文件"),
            ("http://fgw.sh.gov.cn/zcwj03/", "发改委-上海-社会发展政策文件", "政府文件"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, category, classify in urls:
            yield scrapy.Request(url, meta={'category': category, 'classify': classify},
                                 callback=self.parse, headers=HEADERS)

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {'category': category, 'classify': classify}
        pager = JsPage(response.text)
        next_page = pager.next_page(response.url)
        page_exists = response.xpath('//div[@class="xwzx_list"]//li/a')
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
        print('next_page', next_page, meta)
        if next_page:
            yield scrapy.Request(next_page, callback=self.parse, headers=HEADERS, meta=meta)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        item = self.zhengce_style(response)

        source_module = '-'.join(response.xpath('//div[@class="xwzx_loc"]/a/text()').extract()[1:]).replace('>', '')
        doc_no = item['extension']['doc_no']
        doc_no = format_doc_no(doc_no)
        item['extension']['doc_no'] = doc_no
        item['file_type'] = format_file_type(doc_no)
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        item['classify'] = response.meta.get('classify')
        item['category'] = response.meta.get('category')
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
        item = PolicyReformItem()
        theme = effective_start = write_time = effective_end = publish_time = doc_no = index_no = source = ''
        title = response.xpath('//*[@id="ivs_title"]/h3/text()').extract_first(default='').strip()
        table = response.xpath('//div[@class="xwzx_time1"]/ul/li')
        for i in table:
            text = i.xpath('./text()').extract_first(default='')
            key = re.sub(r'\s', '', text.split('：')[0])
            value = text.split('：')[-1].strip()
            # print(key, value)
            if '索取号' in key:
                index_no = value
            elif '发布日期' in key:
                publish_time = time_map(value)
            elif '主题词' in key:
                theme = value
            elif '文号' in key:
                doc_no = value
            elif '发布机关' in key:
                source = value

        content_str = '//*[@id="ivs_content"]'
        content = xpath_from_remove(response, 'string({})'.format(content_str)).strip()

        html_content = get_html_content(response, content_str).strip()
        # 附件信息
        attach_str = '{}//a[not(@href="javascript:void(0);")]'
        attach = response.xpath('{}|{}'.format(
            attach_str.format(content_str), attach_str.format('//div[@class="xglj_list"]')))

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
    $(".pagination").pagination("setPage",2,6);
    """

    def __init__(self, response: str, re_str='\$\("\.pagination"\)\.pagination(.*?);'):
        # createPageHTML(89, 1,"index", "shtml",  "black2",621);
        self.find = re.findall(r'{}'.format(re_str), response)
        try:
            _, self.now, self.total = eval(self.find[0])
        except:
            self.total = self.now = None
        self.default = 'index'
        self.type = 'html'

    def next_page(self, url):
        if not self.find:
            return None
        elif self.total > self.now:
            base_url = url.split('/')
            base_url[-1] = '{}_{}.{}'.format(self.default, self.now + 1, self.type)
            return '/'.join(base_url)
        else:
            return None
