import requests
import lxml
from lxml import etree
import re


def base_req(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}
    req = requests.get(url, headers=headers, verify=False)
    return req


def load_html(req):
    req_data = req.content.decode()
    return lxml.etree.HTML(req_data)


def crawl_test():
    url = "http://life.city8090.com/shenzhen/daoluming/"
    req = base_req(url)
    my_tree = load_html(req)
    road_list = my_tree.xpath('//div[@class="content_list01"]/ul/li[@class="width01"]')
    for road_item in road_list:
        road_name = road_item.xpath('p[1]/a/text()')
        other_list = road_item.xpath('p[2]/a/text()')
        other_list = [re.sub("\s", "", i) for i in other_list if re.sub("\s", "", i)]

        print(road_name, other_list)


if __name__ == '__main__':
    crawl_test()
