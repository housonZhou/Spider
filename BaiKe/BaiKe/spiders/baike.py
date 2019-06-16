# -*- coding: utf-8 -*-
import re
import scrapy
from BaiKe.items import BaikeItem
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class BaikeSpider(CrawlSpider):
    name = 'baike'
    allowed_domains = ['baike.baidu.com']
    start_urls = ['https://baike.baidu.com/item/%E8%85%BE%E8%AE%AF/112204']
    rules = [Rule(LinkExtractor(allow="item/.+"), callback="baike_parse", follow=True)]

    def baike_parse(self, response):
        item = BaikeItem()
        url = response.request.url
        page_data = self.base_msg(response)
        if page_data.get("tag"):
            item["url"] = url
            for k, v in page_data.items():
                item[k] = v
            yield item

    def base_msg(self, html_tree):
        word_name = html_tree.xpath('//dd[@class="lemmaWgt-lemmaTitle-title"]/h1/text()').extract()[0]
        msg = html_tree.xpath('//dd[@class="lemmaWgt-lemmaTitle-title"]/h2/text()').extract()
        msg = msg[0] if msg else ""
        same_name = html_tree.xpath('//span[@class="viewTip-fromTitle"]/text()').extract()
        same_name = same_name[0] if same_name else ""
        tag_list = html_tree.xpath('//*[@id="open-tag-item"]//span[@class="taglist"]//text()').extract()
        tag_list = [re.sub("\s", "", i) for i in tag_list if re.sub("\s", "", i)]
        tag = self.get_tag(tag_list)
        summary = html_tree.xpath('string(//div[@class="lemma-summary"])').extract()[0]
        summary = summary.replace("\xa0", "")
        basic_info_list = html_tree.xpath('//div[@class="basic-info cmn-clearfix"]/dl/dt')
        basic_info = {}
        for item in basic_info_list:
            info_name = item.xpath('string(.)').extract()[0]
            info_name = re.sub("\s", "", info_name)
            info_value = item.xpath('string(following-sibling::dd[1])').extract()[0]
            info_value = re.sub("\[.*?\]", "", info_value).strip()
            basic_info[info_name] = info_value
        level_1 = self.level_data('//div[@class="lemma-catalog"]/div//li[@class="level1"]/span[@class="text"]',
                                  html_tree)
        level_2 = self.level_data('//div[@class="lemma-catalog"]/div//li[@class="level2"]/span[@class="text"]',
                                  html_tree)
        data = {"word_name": word_name, "word_msg": msg, "same_name": same_name, "tag": tag, "tag_list": tag_list,
                "basic_info": basic_info, "summary": summary, "level_1": level_1, "level_2": level_2}
        return data

    def get_tag(self, tag_list):
        need = ["科技产品", "公司", "人物", "品牌"]
        for tag in need:
            if tag in tag_list:
                return tag
        return ""

    def level_data(self, e_xpath, html_tree):
        catalog_level = html_tree.xpath(e_xpath)
        le_data = {}
        for catalog in catalog_level:
            level_name = catalog.xpath('string(.)').extract()[0]
            level_name = re.sub("\s", "", level_name)
            level_link = catalog.xpath('a/@href').extract()[0]
            le_data[level_name] = level_link
        return le_data
