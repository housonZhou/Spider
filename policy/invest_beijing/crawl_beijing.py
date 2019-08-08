import re
import requests
import json
from lxml.etree import HTML


def base_post(post_url, **kwargs):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': '_gscu_415207274=65158638f1fu7q73; _gscbrs_415207274=1; UM_distinctid=16c6ab98b2faf-0b3227c4609a1d-'
                  '3a65460c-1fa400-16c6ab98b3054b; _va_ref=%5B%22%22%2C%22%22%2C1565158655%2C%22http%3A%2F%2Finvest.be'
                  'ijing.gov.cn%2Fgb%2FmanageArticle.do%3Fmethod%3Dlist%26catalogCode%3D100101%22%5D; sensorsdata2015'
                  'jssdkcross=%7B%22distinct_id%22%3A%2216c6ab9caa71db-0c6c05357fb5cb-3a65460c-921600-16c6ab9caa8fb%2'
                  '2%7D; _va_id=685e2db2252d5fa6.1565158655.1.1565158787.1565158655.; JSESSIONID=46EB82A9DD180C4B8D37'
                  'D0AA1D391E02; CNZZDATA1261111621=757851447-1565157944-http%253A%252F%252Finvest.beijing.gov.cn%252'
                  'F%7C1565226837; _gscs_415207274=t652306740jodgg11|pv:15'
    }
    data = requests.post(post_url, verify=False, headers=headers, **kwargs)
    return data.content.decode('gb2312')


def base_get(url, **kwargs):
    data = requests.get(url, verify=False, **kwargs)
    return data.content.decode('gb2312')


def page_detail(data):
    tree = HTML(data)
    title = tree.xpath('//td[@class="hh"]/text()')
    time_map = tree.xpath('//*[@id="yn"]/tr/td[@align="right"]/text()')
    content = tree.xpath('string(//*[@id="ce"])').strip()
    return {'title': title[0] if title else '',
            'time_map': time_map[0].strip() if time_map else '',
            'content': content}


def page_list(tree: HTML):
    for item in tree.xpath('//*[@id="artList"]/tr'):
        title = item.xpath('td[1]/a/text()')
        url_id = item.xpath('td[1]/a/@id')
        time_map = item.xpath('td[2]/text()')
        if time_map:
            time_map = re.findall('\d{4}\D\d{2}\D\d{2}', time_map[0])
        yield {'title': title[0] if title else '', 'url_id': url_id[0] if url_id else '',
               'time_map': time_map[0] if time_map else ''}


def start():
    save_path = r'C:\Users\17337\houszhou\data\SpiderData\政策\0808\北京投资.json'
    file = open(save_path, 'w', encoding='utf8')
    for i in range(1, 19):
        url = 'http://invest.beijing.gov.cn/gb/manageArticle.do?method=list&page={}&catalogCode=100101002'.format(i)
        print(url)
        index_data = base_get(url)
        index_tree = HTML(index_data)
        try:
            for item in page_list(index_tree):
                print(item)
                url_id = item.get('url_id')
                title = item.get('title')
                time_map = item.get('time_map')
                post_url = 'http://invest.beijing.gov.cn/gb/showArticle.do?articleId={}'.format(url_id)
                try:
                    page_data = base_post(post_url)
                    detail = page_detail(page_data)
                    if not detail.get('title'):
                        detail['title'] = title
                    if not detail.get('time_map'):
                        detail['time_map'] = time_map
                    detail['url'] = post_url
                    file.write(json.dumps(detail, ensure_ascii=False) + '\n')
                    file.flush()
                    print('save data')
                except Exception as e:
                    print(e)
                    print('item error: ', item)
        except Exception as e:
            print(e)
            print('page error', url)
    file.close()


def test():
    # url = '107837'
    # data = base_post(url)
    # print(page_detail(data))
    url = 'http://invest.beijing.gov.cn/gb/manageArticle.do?method=list&page=1&catalogCode=100101002'
    data = base_get(url)
    print(data)
    for item in page_list(HTML(data)):
        print(item)


if __name__ == '__main__':
    start()
