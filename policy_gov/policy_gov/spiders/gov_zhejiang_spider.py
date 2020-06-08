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
    GovBeiJingPageControl, find_effective_start, format_file_type, format_doc_no


class GovZheJiangSpider(scrapy.Spider):
    name = 'GovZheJiangSpider'
    other_url = "http://www.zj.gov.cn/module/jpage/dataproxy.jsp?startrecord={}&endrecord={}&perpage=15"
    base_url = 'http://www.zj.gov.cn/module/jpage/morecolumndataproxy.jsp?startrecord={}&endrecord={}&perpage=15'

    project_hash = 'policy_gov0508'
    website = '浙江省人民政府'
    # classify = '政府文件'

    area_data = {
        'col': '1',
        'appid': '1',
        'webid': '3096',
        'path': '/',
        'columnid': '1545733',
        'sourceContentType': '1',
        'unitid': '4767824',
        'webname': '浙江省人民政府门户网站',
        'permissiontype': '0'
    }

    regulations_data = {
        'infotypeId': 'C0101',
        'jdid': '3096',
        'area': '000014349',
        'divid': 'div1545734',
        'vc_title': '',
        'vc_number': '',
        'sortfield': ',compaltedate:0',
        'currpage': '1',
        'vc_filenumber': '',
        'vc_all': '',
        'texttype': '0',
        'fbtime': '',
    }
    specification_data = {
        'infotypeId': 'C0102',
        'jdid': '3096',
        'area': '000014349',
        'divid': 'div1228964496',
        'vc_title': '',
        'vc_number': '',
        'sortfield': ',compaltedate:0',
        'currpage': '1',
        'vc_filenumber': '',
        'vc_all': '',
        'texttype': '0',
        'fbtime': '',
    }

    data = {'gov': regulations_data, 'dept': specification_data}

    headers = HEADERS.copy()
    headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'http://www.zj.gov.cn/col/col1545736/index.html',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': 'zh_choose_undefined=s; SERVERID=a6d2b4ba439275d89aa9b072a5b72803|1588815036|1588814667'
    })

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(FILES_STORE, today)
    if not os.path.exists(date_dir):
        os.mkdir(date_dir)

    def start_requests(self):
        urls = [
            ("http://www.zj.gov.cn/module/xxgk/search.jsp",
             "", "人民政府-浙江-政府规章", "地方行政规章", "gov"),
            ("http://www.zj.gov.cn/module/xxgk/search.jsp",
             "", "人民政府-浙江-行政规范性文件", "政府文件", "dept"),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, source_module, category, classify, data in urls:
            post_data = self.data.get(data).copy()
            yield scrapy.FormRequest(url, formdata=post_data, callback=self.parse, headers=self.headers,
                                     meta={"source_module": source_module, 'category': category,
                                           'classify': classify, 'data': data}, dont_filter=True)

        area_urls = [
            (self.other_url.format(1, 45), "人民政府-浙江-地方性法规", "地方行政规章",
             {'columnid': '1229005922', 'sourceContentType': '1', 'unitid': '5645417'}),
            (self.base_url.format(1, 45), "人民政府-浙江-计划总结", "年度工作计划及总结",
             {'columnid': '1551811,1552031,1552227,1552322,1552523,1552634,1553142,1553192,1553003,1552951,1552809,'
                          '1552711,1552688,1553367,1553482,1554323,1553703,1553773,1554029,1553823,1553735,1552921,'
                          '1554238,1553936,1554299,1554436,1554344,1553984,1654348,1228965213',
              'sourceContentType': '3', 'unitid': '4907049', 'keyWordCount': '999'}),
            (self.base_url.format(1, 45), "人民政府-浙江-政策解读", "部门解读",
             {'columnid': '1229019366', 'sourceContentType': '3', 'unitid': '5469141', 'keyWordCount': '999'}),
            (self.base_url.format(1, 45), "人民政府-浙江-规划信息", "发展计划",
             {'columnid': '1568483,1568484,1568485,1551754,1551791,1552030,1552226,1552521,1552614,1552707,1552708,'
                          '1552709,1553269,1553077,1553005,1552975,1552861,1553869,1552730,1553509,1554261,1553704,'
                          '1553774,1553824,1554239,1553937,1554300,1554434,1554219,1554054',
              'sourceContentType': '3', 'unitid': '4907031', 'keyWordCount': '999'}),
        ]
        # self.cookies = get_cookie('http://www.hubei.gov.cn/xxgk/gsgg/')
        for url, category, classify, data in area_urls:
            post_data = self.area_data.copy()
            post_data.update(data)
            print(url)
            print(post_data)
            yield scrapy.FormRequest(url, formdata=post_data, callback=self.parse_area, headers=self.headers,
                                     meta={'category': category, 'classify': classify, 'data': data})

    def parse(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        source_module = response.meta.get('source_module')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        data = response.meta.get('data')
        meta = {"source_module": source_module, 'category': category, 'classify': classify, 'data': data}
        next_page = response.xpath(
            '//td[@align="right"]/a[contains(text(), "下一页")]/@href').extract_first()
        next_page = int(obj_first(re.findall(r'\d+', next_page)))
        end_page = response.xpath(
            '//td[@align="right"]/a[contains(text(), "尾 页")]/@href').extract_first()
        end_page = int(obj_first(re.findall(r'\d+', end_page)))
        page_exists = response.xpath('//a[@gkfs="主动公开"]')
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
        # print('next_page', next_page, end_page, meta)
        if next_page <= end_page:
            next_url = 'http://www.zj.gov.cn/module/xxgk/search.jsp'
            post_data = self.data.get(data).copy()
            post_data["currpage"] = str(next_page)
            yield scrapy.FormRequest(next_url, formdata=post_data, callback=self.parse,
                                     headers=self.headers, meta=meta, dont_filter=True)

    def parse_area(self, response: scrapy.http.Response):
        conn = RedisConnect().conn
        content = response.text
        data = response.meta.get('data')
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        meta = {"data": data, 'category': category, 'classify': classify}
        start = int(obj_first(re.findall(r'startrecord=(\d+)', response.url)))
        end = int(obj_first(re.findall(r'endrecord=(\d+)', response.url)))
        total = int(obj_first(re.findall(r'<totalrecord>(\d+)</totalrecord>', content)))
        if end < total:
            base_url = self.other_url if category == '人民政府-浙江-地方性法规' else self.base_url
            next_url = base_url.format(start + 45, end + 45)
        else:
            next_url = ''
        #     page_exists = response.xpath('//ul[@class="uli14 pageList "]/li/a')
        result = re.findall(r"href='(.*?)'", content) or re.findall(r'href="(.*?)"', content)
        for item in result:
            url = response.urljoin(item)
            if RUN_LEVEL == 'FORMAT':
                if conn.hget(self.project_hash, category + '-' + url):
                    return
                else:
                    conn.hset(self.project_hash, category + '-' + url, 1)
            # print(url, meta)
            yield scrapy.Request(url, callback=self.parse_detail, headers=HEADERS, meta=meta)
        # print('next_page', next_url, meta)
        if next_url:
            post_data = self.area_data.copy()
            post_data.update(data)
            yield scrapy.FormRequest(next_url, formdata=post_data, callback=self.parse_area,
                                     headers=self.headers, meta=meta, dont_filter=True)

    def parse_detail(self, response: scrapy.http.Response):
        row_id = hashlib.md5(response.url.encode()).hexdigest()
        if response.xpath('//div[@class="contbox"]'):
            item = self.news_style(response)
        else:
            item = self.zhengce_style(response)
        word = response.xpath('//div[@class="dqwz"]/div//a/text()').extract()
        source_module = '-'.join(i.strip() for i in word if i.strip())

        doc_no = item['extension']['doc_no']
        doc_no = format_doc_no(doc_no)
        item['extension']['doc_no'] = doc_no
        item['file_type'] = format_file_type(doc_no)
        item['row_id'] = row_id
        item['website'] = self.website
        item['source_module'] = source_module
        item['url'] = response.url
        classify = response.meta.get('classify')
        category = response.meta.get('category')
        title = item['title']
        if category == '人民政府-浙江-地方性法规' and '人民代表大会' in title:
            classify = '地方性法规'
        elif category == '人民政府-浙江-规划信息' and '报告' in title:
            classify = '年度工作计划及总结'
        item['classify'] = classify
        item['category'] = category
        # item['publish_time'] = publish_time
        # item['html_content'] = html_content
        for index, file_name in enumerate(item['extension'].get('file_name')):
            file_url = item['extension'].get('file_url')[index]
            file_type = os.path.splitext(file_url.split('/')[-1])[-1]
            file_name_type = os.path.splitext(file_name)[-1]
            if (not file_name_type) or re.findall(r'[^\.a-zA-Z0-9]', file_name_type) or len(file_name_type) > 7:
                file_name = file_name + file_type
            file_name = "{}_{}".format(index, file_name)
            item['extension']['file_name'][index] = file_name
            meta = {'row_id': row_id, 'file_name': file_name}
            # print(response.url, file_url, meta)
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
        write_time = effective_start = effective_end = theme = ''
        table_str = '//table[@class="fgwj_xxgk_head"]'
        if not response.xpath(table_str):
            table_str = '//table[@class="xxgk_top"]'
        title = response.xpath('//*[@class="title"]/text()|//*[@class="art_title"]/h2/text()').extract_first().strip()
        source = response.xpath('{}/tbody/tr[2]/td[2]/text()'.format(table_str)).extract_first(default='')
        doc_no = response.xpath('{}/tbody/tr[4]/td[2]/text()'.format(table_str)).extract_first(default='')
        publish_time = time_map(response.xpath('{}/tbody/tr[2]/td[4]/text()'.format(table_str)).extract_first())
        index_no = response.xpath('{}/tbody/tr[1]/td[2]/text()'.format(table_str)).extract_first(default='')
        exclusive_sub = response.xpath('{}/tbody/tr[1]/td[4]/text()'.format(table_str)).extract_first(default='')

        content_str = '//div[@class="bt_content"]//div[@class="bt_content"]'
        if not response.xpath(content_str):
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
            if (not url_) or re.findall(r'baidu|javascript|html', url_):
                continue
            extension['file_name'].append(file_name)
            extension['file_url'].append(download_url)
            if re.findall(r'htm|ewT\.aspx\?', url_):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')
        # var pdfurl = "/module/download/downfile.jsp?filename=b796d1a595774c7bb5b8cd9e4cca8a82.pdf&classid=0";
        pdf_url = re.findall(r'var pdfurl = "(.+?)";', response.text)
        if pdf_url:
            pdf_url = pdf_url[0]
            file_name = re.findall(r'filename=(.*?)&', pdf_url)
            if file_name:
                extension['file_name'].append(file_name[0])
                extension['file_url'].append(response.urljoin(pdf_url))
                extension['file_type'].append('')

        attach_img = response.xpath('{}//img[not(@href="javascript:void(0);")]'.format(content_str))
        img_name = 'none'
        for a in attach_img:
            file_name = a.xpath('./@{}'.format(img_name)).extract_first()
            url_ = a.xpath('./@src').extract_first()
            if not url_ or url_.split('.')[-1].lower() in IMG_ERROR_TYPE or re.findall(r'jslib|picture|\{.*?\}', url_):
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
        extension['effective_end'] = effective_end
        extension['is_effective'] = effective(effective_start, effective_end)
        item['content'] = content
        item['title'] = title
        item['source'] = source if source else self.website
        item['publish_time'] = publish_time
        item['html_content'] = html_content
        item['extension'] = extension
        return item

    def news_style(self, response):
        item = PolicyReformItem()
        write_time = effective_start = effective_end = doc_no = index_no = theme = exclusive_sub = ''
        title = response.xpath('string(//div[@class="contbox"]//tr[1])').extract_first().strip()
        other = response.xpath('string(//div[@class="contbox"]//tr[2])').extract_first(default='').strip()
        source = obj_first(re.findall(r'来源：(\S*)', other))
        publish_time = time_map(other)

        content_str = '//div[@class="contbox"]//td[@class="bt_content"]'
        if not response.xpath(content_str):
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
            if re.findall(r'htm|ewT\.aspx\?', url_):
                extension['file_type'].append('url')
            else:
                extension['file_type'].append('')

        attach_img = response.xpath('{}//img[not(@href="javascript:void(0);")]'.format(content_str))
        img_name = 'none'
        for a in attach_img:
            file_name = a.xpath('./@{}'.format(img_name)).extract_first()
            url_ = a.xpath('./@src').extract_first()
            if not url_ or url_.split('.')[-1].lower() in IMG_ERROR_TYPE or re.findall(r'jslib|picture|\{.*?\}', url_):
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

