import json
import re
import time

from lxml.etree import HTML

from intellectual_property.tools import base_req


def post(page_num, **kwargs):
    url = 'http://ipr.mofcom.gov.cn/ipr/front/www/listN'
    data = {'pageNumber': str(page_num), 'cid': 'gnxw'}
    headers = {
        'Host': 'ipr.mofcom.gov.cn',
        'Connection': 'keep-alive',
        'Content-Length': '21',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': 'http://ipr.mofcom.gov.cn',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'http://ipr.mofcom.gov.cn/list/gnxw/1/cateinfo.html',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        # 'Cookie': 'insert_cookie=44501640'
    }
    return base_req('POST', url, data=data, headers=headers, **kwargs)


def get(url, **kwargs):
    headers = {
        'Host': 'ipr.mofcom.gov.cn',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Referer': 'http://ipr.mofcom.gov.cn/list/gnxw/1/cateinfo.html',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        # 'Cookie': 'insert_cookie=44501640'
    }
    return base_req(method='GET', url=url, headers=headers, **kwargs)


def page_list(resp):
    if not resp:
        return
    resp_data = resp.content.decode()
    resp_data = json.loads(resp_data)
    page_info = resp_data.get('pageInfo')
    for each in page_info.get('rows'):
        # article_id = each.get('article_id')
        time_str = each.get('publishTimeStr')
        title = each.get('title')
        url = each.get('url')
        if not url.startswith('http'):
            url = 'http://ipr.mofcom.gov.cn' + url
        yield {'time_str': time_str, 'title': title, 'url': url}


def page_detail(url):
    resp = get(url)
    if not resp:
        return {}
    resp_data = resp.content.decode()
    tree = HTML(resp_data)
    title = re.findall(r'var title = \'(.*?)\'\;', resp_data)
    source = re.findall(r'var source = \'(.*?)\'\;', resp_data)
    content = tree.xpath('//section[@class="artCon"]/p/text()')
    return {'title': title[0] if title else '', 'source': source[0] if source else '', 'content': '\n'.join(content)}


def save(data=None):
    path = r'C:\Users\17337\houszhou\data\SpiderData\知识产权\中国保护知识产权网\中国保护知识产权网.json'
    data = data.copy()
    with open(path, 'a', encoding='utf8')as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')


def main():
    source_default = '中国保护知识产权网'
    for i in range(1, 601):
        try:
            list_result = post(page_num=i)
            for item in page_list(list_result):
                try:
                    page_result = page_detail(item.get('url'))
                    title = page_result.get('title') if page_result.get('title') else item.get('title')
                    source = page_result.get('source') if page_result.get('source') else source_default
                    save_data = {'title': title, 'source': source, 'publish_date': item.get('time_str'),
                                 'content': page_result.get('content'), 'link': item.get('url')}
                    print(save_data)
                    save(data=save_data)
                except Exception as e:
                    print(e)
                finally:
                    time.sleep(1)
        except Exception as e:
            print(e)


def test():
    # result = post(page_num=600)
    # for i in page_list(result):
    #     print(i)
    url = '/article/gnxw/zfbm/zfbmdf/js/201911/1944269.html'
    resp = get(url)
    print(page_detail(resp))


if __name__ == '__main__':
    main()
