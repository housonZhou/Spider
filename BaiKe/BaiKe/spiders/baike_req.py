import requests
import lxml
import random
import re
import urllib.parse
from lxml import etree
from fake_useragent import UserAgent


def base_req(url):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    print(headers)
    req = requests.get(url, headers=headers, verify=False)
    return req


def load_html(req):
    req_data = req.content.decode()
    return lxml.etree.HTML(req_data)


def get_tag(tag_list):
    need = ["科技产品", "公司", "人物", "品牌"]
    for tag in need:
        if tag in tag_list:
            return tag
    return ""


def base_msg(html_tree):
    word_name = html_tree.xpath('//dd[@class="lemmaWgt-lemmaTitle-title"]/h1/text()')[0]
    msg = html_tree.xpath('//dd[@class="lemmaWgt-lemmaTitle-title"]/h2/text()')
    msg = msg[0] if msg else ""
    same_name = html_tree.xpath('//span[@class="viewTip-fromTitle"]/text()')
    same_name = same_name[0] if same_name else ""
    tag_list = html_tree.xpath('//*[@id="open-tag-item"]//span[@class="taglist"]//text()')
    tag_list = [re.sub("\s", "", i) for i in tag_list if re.sub("\s", "", i)]
    tag = get_tag(tag_list)
    summary = html_tree.xpath('string(//div[@class="lemma-summary"])')
    summary = summary.replace("\xa0", "")
    basic_info_list = html_tree.xpath('//div[@class="basic-info cmn-clearfix"]/dl/dt')
    basic_info = {}
    for item in basic_info_list:
        info_name = item.xpath('string(.)')
        info_name = re.sub("\s", "", info_name)
        info_value = item.xpath('string(following-sibling::dd[1])')
        info_value = re.sub("\[.*?\]", "", info_value).strip()
        basic_info[info_name] = info_value
    catalog_level1 = html_tree.xpath('//div[@class="lemma-catalog"]/div//li[@class="level1"]/span[@class="text"]')
    for catalog in catalog_level1:
        level1_name = catalog.xpath('string(.)')
        level1_name = re.sub("\s", "", level1_name)
        level1_link = catalog.xpath('a/@href')
        print(level1_name, level1_link)
    catalog_level2 = html_tree.xpath('//div[@class="lemma-catalog"]/div//li[@class="level2"]/span[@class="text"]')
    for catalog in catalog_level2:
        level2_name = catalog.xpath('string(.)')
        level2_name = re.sub("\s", "", level2_name)
        level2_link = catalog.xpath('a/@href')
        print(level2_name, level2_link)

    data = {"word_name": word_name, "word_msg": msg, "same_name": same_name, "tag": tag, "tag_list": tag_list,
            "basic_info": basic_info, "summary": summary}
    return data


def summary_data(html_tree):
    dom_str = html_tree.xpath('//div[@class="lemma-summary"]')
    dom = lxml.etree.tostring(dom_str[0]).decode("utf8")
    print(dom)
    new_str = re.sub("\<[a-z]{2,}.*?\>", "", dom)
    new_str = re.sub("\<\/[a-z]{2,}.*?\>", "", new_str)
    print(new_str)


def crawl_test():
    # word = "深圳市腾讯计算机系统有限公司"
    # url = "https://baike.baidu.com/item/ofo%E5%B0%8F%E9%BB%84%E8%BD%A6/20808277?fromtitle=ofo%E5%85%B1%E4%BA%AB%E5%8D%95%E8%BD%A6&fromid=19499162"  # ofo
    # url = "https://baike.baidu.com/item/%E8%85%BE%E8%AE%AF?fromtitle=%E8%85%BE%E8%AE%AF%E5%85%AC%E5%8F%B8&fromid=355135"  # 腾讯
    # url = "https://baike.baidu.com/item/ofo%E5%B0%8F%E9%BB%84%E8%BD%A6/20808277?fromtitle=OFO&fromid=20104243"  # ufo
    # url = "https://baike.baidu.com/item/%E8%81%94%E6%83%B3%E7%94%B5%E8%84%91/334647"  # 联想
    # url = "https://baike.baidu.com/item/%E6%AC%A7%E8%8E%B1%E9%9B%85%EF%BC%88%E6%B3%95%E5%9B%BD%EF%BC%89%E5%8C%96%E5%A6%86%E5%93%81%E9%9B%86%E5%9B%A2%E5%85%AC%E5%8F%B8?fromtitle=%E6%AC%A7%E8%8E%B1%E9%9B%85&fromid=1216896"  # 欧莱雅
    url = "https://baike.baidu.com/item/%E4%B8%AD%E5%9B%BD/1122445"  # 中国
    # url = "https://baike.baidu.com/item/%E6%9D%A8%E5%B9%82"
    req = base_req(url)
    my_tree = load_html(req)
    data = summary_data(my_tree)
    # print(data)


if __name__ == '__main__':
    crawl_test()
