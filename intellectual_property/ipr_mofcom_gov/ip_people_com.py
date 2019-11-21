import json
import re
import time

from lxml.etree import HTML

from intellectual_property.tools import base_req, get_first


def get(url, **kwargs):
    headers = {
        'Host': 'ip.people.com.cn',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Referer': 'http://ip.people.com.cn/GB/179663/index1.html',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    return base_req(method='GET', url=url, headers=headers, **kwargs)


def page_list(page_num):
    url = 'http://ip.people.com.cn/GB/179663/index{}.html'.format(page_num)
    print(url)
    resp = get(url)
    if not resp:
        return
    resp_data = resp.content.decode('utf8', errors='ignore')
    tree = HTML(resp_data)
    url_list = tree.xpath('//div[@class="ej_list_box clear"]/ul/li/a/@href')
    return ('http://ip.people.com.cn' + i for i in url_list)


def page_detail(url):
    source_default = '人民网'
    resp = get(url)
    if not resp:
        return {}
    resp_data = resp.content.decode('gb2312', errors='ignore')
    tree = HTML(resp_data)
    title = tree.xpath('//h1/text()')
    info = tree.xpath('string(//div[@class="box01"]/div[@class="fl"])')
    source = re.findall('来源：(.*)', info)
    time_str = re.findall(r'(\d{4}\D\d+\D\d+\D)', info)
    content = tree.xpath('string(//*[@id="rwb_zw"])')
    return {'title': get_first(title), 'source': get_first(source, source_default), 'publish_date': get_first(time_str),
            'content': content.strip(), 'link': url}


def save(data=None):
    path = r'C:\Users\17337\houszhou\data\SpiderData\知识产权\中国保护知识产权网\人民网.json'
    data = data.copy()
    with open(path, 'a', encoding='utf8')as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')


def one_list(page_num):
    for page_url in page_list(page_num):
        try:
            page_result = page_detail(page_url)
            print(page_result)
            save(data=page_result)
        except Exception as e:
            print(page_url, e)
        finally:
            time.sleep(1)


def main():
    for i in range(1, 8):
        try:
            one_list(i)
        except Exception as e:
            print(e)


def test():
    pass
    # print(len(list(page_list('1'))))
    print(page_detail('http://ip.people.com.cn/n1/2019/1114/c179663-31455432.html'))


if __name__ == '__main__':
    main()
