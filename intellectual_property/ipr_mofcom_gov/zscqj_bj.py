import json
import re
import time
from itertools import chain

from lxml.etree import HTML

from intellectual_property.tools import base_req, get_first


def get(url, **kwargs):
    headers = {
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Referer': 'http://zscqj.beijing.gov.cn/zwxx/mtbd/pc_index_list.html',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    return base_req(method='GET', url=url, headers=headers, **kwargs)


def page_list(page_num):
    url = 'http://zscqj.beijing.gov.cn/zwxx/mtbd/pc_index_list{}.html'.format(page_num)
    print(url)
    resp = get(url)
    if not resp:
        return
    resp_data = resp.content.decode('utf8', errors='ignore')
    tree = HTML(resp_data)
    url_list = tree.xpath('//ul[@class="subpageCon-conList"]/li')
    for item in url_list:
        page_url = get_first(item.xpath('a/@href'))
        title = get_first(item.xpath('a/text()'))
        time_str = get_first(item.xpath('span/text()'))
        yield page_url, title, time_str


def page_class(info):
    source_default = '北京知识产权局'
    url, title, time_str = info
    title_split = re.split('：', title)
    if len(title_split) == 1:
        title_split = re.split(':', title)
    if len(title_split) == 1:
        source = source_default
        page_title = title_split[0]
    else:
        source = title_split[0]
        page_title = ''.join(title_split[1:])
    if 'weixin' in url:
        class_ = 'weixin'
    elif 'iprchn.com' in url:
        class_ = 'iprchn'
    elif 'http' not in url:
        class_ = 'zscqj'
        url = 'http://zscqj.beijing.gov.cn' + url
    else:
        class_ = 'pass'
    return url, source, page_title, class_, time_str


def page_detail(url, class_):
    resp = get(url)
    if not resp:
        return {}
    resp_data = resp.content.decode(errors='ignore')
    tree = HTML(resp_data)
    if class_ == 'weixin':
        content = tree.xpath('string(//*[@id="js_content"])').strip()
    elif class_ == 'zscqj':
        content = tree.xpath('string(//div[@class="article-word"])').strip()
    else:
        content = tree.xpath('//span/text()')
        content = '\n'.join(i.strip() for i in content if i.strip())
    return content


def save(data=None):
    path = r'C:\Users\17337\houszhou\data\SpiderData\知识产权\中国保护知识产权网\北京知识产权局.json'
    data = data.copy()
    with open(path, 'a', encoding='utf8')as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')


def one_list(page_num):
    for page_info in page_list(page_num):
        try:
            url, source, page_title, class_, time_str = page_class(page_info)
            if class_ == 'pass':
                continue
            content = page_detail(url, class_)
            page_result = {'title': page_title, 'source': source.strip(), 'publish_date': time_str,
                           'content': content, 'link': url}
            print(page_result)
            save(data=page_result)
        except Exception as e:
            print(page_info, e)
        finally:
            time.sleep(1)


def main():
    for i in chain([''], ('_{}'.format(i) for i in range(2, 7))):
        try:
            one_list(i)
        except Exception as e:
            print(e)


def test():
    pass
    # print(len(list(page_list('1'))))
    # print(page_detail('http://ip.people.com.cn/n1/2019/1114/c179663-31455432.html'))
    # url = 'http://zscqj.beijing.gov.cn/zwxx/mtbd/pc_index_list'
    # print(get(url))
    # url = 'http://www.iprchn.com/cipnews/news_content.aspx?newsId=117609'
    # print(detail_weixin(url, ''))


if __name__ == '__main__':
    main()
