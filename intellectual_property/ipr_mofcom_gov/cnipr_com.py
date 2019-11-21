import json
import re
import time

from lxml.etree import HTML

from intellectual_property.tools import base_req


def get(url, **kwargs):
    headers = {
        'Host': 'www.cnipr.com',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Referer': 'http://www.cnipr.com/index.html',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    return base_req(method='GET', url=url, headers=headers, **kwargs)


def page_list(resp):
    if not resp:
        return
    resp_data = resp.content.decode()
    tree = HTML(resp_data)
    url_list = tree.xpath('//div[@class="article_list"]//h1/a/@href')
    return (re.sub(r'^\.', 'http://www.cnipr.com', i) for i in url_list)


def page_detail(url):
    resp = get(url)
    if not resp:
        return {}
    resp_data = resp.content.decode()
    tree = HTML(resp_data)
    title = tree.xpath('//div[@class="xq_cont_title"]/p[@class="alxq_title1"]/text()')
    time_str = tree.xpath('//div[@class="time list1_dongtai_time"]/span/text()')
    time_str = re.findall(r'(\d{4}\D\d+\D\d+)', time_str[0]) if time_str else ['']
    source = tree.xpath('//div[@class="dianzan"]/span/text()')
    source = source[0].split('：')[-1]
    content = tree.xpath('string(//div[@class="TRS_Editor"])')
    return {'title': title[0] if title else '', 'source': source, 'content': content, 'time_str': time_str[0]}


def save(data=None):
    path = r'C:\Users\17337\houszhou\data\SpiderData\知识产权\中国保护知识产权网\中国知识产权网.json'
    data = data.copy()
    with open(path, 'a', encoding='utf8')as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')


def one_list(page_num):
    source_default = '中国知识产权网'
    url = 'http://www.cnipr.com/index{}.html'.format(page_num)
    list_result = get(url)
    for page_url in page_list(list_result):
        try:
            page_result = page_detail(page_url)
            source = page_result.get('source') if page_result.get('source') else source_default
            save_data = {
                'title': page_result.get('title'), 'source': source, 'link': page_url,
                'publish_date': page_result.get('time_str'), 'content': page_result.get('content'),
            }
            print(save_data)
            save(data=save_data)
        except Exception as e:
            print(url, e)
        finally:
            time.sleep(1)


def main():
    for i in ['', '_1', '_2', '_3']:
        try:
            one_list(i)
        except Exception as e:
            print(e)


def test():
    pass
    # url = 'http://www.cnipr.com/index{}.html'.format('')
    # list_result = get(url)
    # for page_url in page_list(list_result):
    #     print(page_url)
    # url = 'http://www.cnipr.com/sj/zx/201911/t20191118_236277.html'
    # print(page_detail(url))
    # one_list('')


if __name__ == '__main__':
    main()
