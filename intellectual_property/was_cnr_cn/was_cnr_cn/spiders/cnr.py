# -*- coding: utf-8 -*-
import scrapy
from lxml.etree import HTML

from intellectual_property.was_cnr_cn.was_cnr_cn.settings import HEADERS
from intellectual_property.was_cnr_cn.was_cnr_cn.items import WasCnrCnItem


class CnrSpider(scrapy.Spider):
    name = 'cnr'
    allowed_domains = ['cnr.com', 'cnr.cn']
    key_words = ['知识产权政策', '质押融资', '知产证券化', '营商环境', '地理标志', '知识产权保护', '知识产权托管',
                 '知识产权评估', '世界知识产权日', '知识产权侵权', '外商投资法', '工业军民融合', '技术转移',
                 '科技成果转化', '知识产权强国', '高价值专利', '配套服务', '粤港澳（大）湾区']
    base_url = 'http://was.cnr.cn/was5/web/search?page={page}&channelid=234439&searchword={word}&keyword={word}&' \
               'orderby=LIFO&perpage=200&outlinepage=200&searchscope=&timescope=&timescopecolumn=&orderby=LIFO&' \
               'andsen=&total=&orsen=&exclude='

    def start_requests(self):
        for word in self.key_words:
            meta = {'page': 1, 'word': word}
            url = self.base_url.format(**meta)
            yield scrapy.Request(url, callback=self.parse, headers=HEADERS, meta=meta)

    def parse(self, response: scrapy.http.Response):
        tree = response
        url_list = tree.xpath('//td[@class="searchresult"]/ol/li')
        for item in url_list:
            try:
                page_url = item.xpath('div[1]/a/@href').extract_first()
                title = item.xpath('string(div[1]/a)').extract_first()
                time_str = item.xpath('div[2]/text()').extract()[-1].strip()
                if time_str.startswith('2019') and '新闻和报纸摘要' not in title:
                    meta = {'title': title, 'publish_date': time_str}
                    yield scrapy.Request(page_url, callback=self.page_detail, headers=HEADERS, meta=meta)
            except:
                pass
        next_url = tree.xpath('//a[@class="next-page"]/@href').extract()
        if next_url:
            meta = {'page': response.meta.get('page') + 1, 'word': response.meta.get('word')}
            url = self.base_url.format(**meta)
            yield scrapy.Request(url, callback=self.parse, headers=HEADERS, meta=meta)

    def page_detail(self, response: scrapy.http.Response):
        item = WasCnrCnItem()
        clear_tag_list = ['style', 'script', 'img', 'button', 'footer', 'input', 'select', 'option',
                          'label', 'blockquote', 'noscript']
        tree = HTML(response.body.decode('gb2312', errors='replace'))
        try:
            source = tree.xpath('//div[@class="source"]/span[2]/text()')[0].replace('来源：', '')
        except:
            source = '央广网'
        for tar in clear_tag_list:
            for dom in tree.findall('.//{}'.format(tar)):
                dom.text = ""
        content = tree.xpath('string(//div[@class="TRS_Editor"])')
        if not content:
            content = tree.xpath('string(//div[@class="article-body"])')
        if not content:
            content = tree.xpath('string(//div[@class="contentText"])')
        if content.strip():
            item.update({
                'title': response.meta.get('title'),
                'publish_date': response.meta.get('publish_date'),
                'source': source,
                'content': content.strip(),
                'link': response.url,
            })
            yield item
