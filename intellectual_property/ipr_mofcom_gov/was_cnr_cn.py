from lxml.etree import HTML

from intellectual_property.tools import base_req, get_first


def get(url, **kwargs):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    return base_req(method='GET', url=url, headers=headers, **kwargs)


def page_list(page_num):
    url = 'http://was.cnr.cn/was5/web/search?page={page}&channelid=234439&searchword={word}&keyword={word}&orderby=' \
          'LIFO&perpage=50&outlinepage=50&searchscope=&timescope=&timescopecolumn=&orderby=LIFO&andsen=&total=&orsen' \
          '=&exclude='.format(page=page_num, word='知识产权政策')
    print(url)
    resp = get(url)
    if not resp:
        return
    resp_data = resp.content.decode('utf8', errors='ignore')
    tree = HTML(resp_data)
    url_list = tree.xpath('//td[@class="searchresult"]/ol/li')
    for item in url_list:
        page_url = get_first(item.xpath('div[1]/a/@href'))
        title = item.xpath('string(div[1]/a)')
        time_str = item.xpath('div[2]/text()')[-1].strip()
        if time_str.startswith('2019') and '新闻和报纸摘要' not in title:
            yield page_url, title, time_str
    next_url = tree.xpath('//a[@class="next-page"]/@href')
    if next_url:
        next_url = 'http://was.cnr.cn/was5/web/' + next_url[0]
        print('next:', next_url)


def page_detail(url):
    clear_tag_list = ['style', 'script', 'img', 'button', 'footer', 'input', 'select', 'option',
                      'label', 'blockquote', 'noscript']
    print(url)
    resp = get(url)
    if not resp:
        return
    resp_data = resp.content.decode('gb2312', errors='replace')
    tree = HTML(resp_data)
    title = tree.xpath('//h2/text()')
    if not title:
        title = tree.xpath('//div[@class="article-header"]/h1/text()')
    source = tree.xpath('//div[@class="source"]/span[2]/text()')[0].replace('来源：', '')
    for tar in clear_tag_list:
        for dom in tree.findall('.//{}'.format(tar)):
            dom.text = ""
    content = tree.xpath('string(//div[@class="TRS_Editor"])')
    if not content:
        content = tree.xpath('string(//div[@class="article-body"])')
    if not content:
        content = tree.xpath('string(//div[@class="contentText"])')
    return title[0], source, content.strip()


def test():
    # for item in page_list(3):
    #     print(item)
    #     url = item[0]
    #     try:
    #         print(page_detail(url))
    #     except Exception as e:
    #         print(url, e)
    url = 'http://www.cnr.cn/china/yaowen/20190427/t20190427_524592815.shtml'
    print(page_detail(url))


if __name__ == '__main__':
    test()
