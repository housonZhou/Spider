import json
import requests
from selenium import webdriver
from selenium.webdriver import ChromeOptions
import codecs
from tools.base_code import RequestTest as Rtest


def demo():
    headers = {'Cookies': '_trs_uv=k7jwffkl_6_7b9v; JSESSIONID=BF5CC2F89E41A077874D0610DAC8524C; u=2; experience=show',
               'X-Requested-With': 'XMLHttpRequest'}
    data = {'id': 'zb', 'dbcode': 'hgnd', 'wdcode': 'zb', 'm': 'getTree'}
    url = 'http://data.stats.gov.cn/easyquery.htm'
    response = Rtest.base_req(url, method='post', headers=headers, data=data)
    print(response.status_code)
    print(response.content.decode())


def post_tree():
    # 第一级
    code_json = {
        '年度': 'hgnd',
        '季度': 'hgjd',
        '月度': 'hgyd',
        '主要城市月度': 'csyd',
        '主要城市年度': 'csnd'
    }
    headers = {'Cookies': '_trs_uv=k7jwffkl_6_7b9v; JSESSIONID=BF5CC2F89E41A077874D0610DAC8524C; u=2; experience=show',
               'X-Requested-With': 'XMLHttpRequest'}
    data = {'id': 'zb', 'dbcode': 'hgnd', 'wdcode': 'zb', 'm': 'getTree'}
    url = 'http://data.stats.gov.cn/easyquery.htm'
    response = Rtest.base_req(url, method='post', headers=headers, data=data)
    resp_data = response.json()
    for item in resp_data:
        print(item)
        id_ = item.get('id')
        isParent = item.get('isParent')
        name = item.get('name')
        wdcode = item.get('wdcode')
        if isParent:
            print('有子标签')


def change():
    from html import escape
    p = r'C:\Users\17337\houszhou\data\SpiderData\国家统计局\done\年度.json'
    with open(p, 'r', encoding='utf8')as f:
        count = 0
        for line in f:
            # count += 1
            # if count > 10:
            #     break
            data = json.loads(line.strip())
            k = data.get('指标单位')
            print(k)
            new = k.encode()
            print(new)
            print()
            break


def post_man():
    url = "http://data.stats.gov.cn/easyquery.htm?m=getOtherWds&dbcode=hgnd&rowcode=zb&colcode=sj&wds=%5B%5D&k1=1585286455856"

    payload = {}
    headers = {
        'Cookie': 'JSESSIONID=B795A41089200A49AC224F6D8018B53F; u=2'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.content)


def driver_run():
    option = ChromeOptions()
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    option.add_argument('--headless')
    # option.add_argument('Accept="application/json;charset=utf-8"')
    driver = webdriver.Chrome(options=option)
    url = "http://data.stats.gov.cn/easyquery.htm?m=getOtherWds&dbcode=hgnd&rowcode=zb&colcode=sj&wds=%5B%5D&k1=1585286455856"
    driver.get(url)
    page = driver.page_source
    print(driver.page_source)
    from lxml.etree import HTML
    tree = HTML(page)
    print(tree.xpath('//pre/text()'))


def cn():
    s = "鏈€杩�5骞�"
    print(s.startswith('最'))
    print(codecs.encode(s, encoding='gbk'))


if __name__ == '__main__':
    cn()
    # sa = '''"exp":"å‚åŠ&nbsp;ä¿é™©äººæ•°æŒ‡æŠ¥å‘ŠæœŸæœ«ä¾æ®å›½å®¶æœ‰å…³è§„å®šå‚åŠ&nbsp;å·¥ä¼¤ä¿é™©çš„èŒå·¥äººæ•°å’Œæœ‰é›‡å·¥çš„ä¸ªä½“å·¥å•†æˆ·çš„é›‡å·¥æ•°ã€‚"'''
    # print(sa)
    # print(type(sa))
    # print(sa.encode('utf','ignore'))
