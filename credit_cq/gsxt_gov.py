import json
import re
import time

import requests
from lxml.etree import HTML
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from tools.base_code import BaseCode

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def retry(count=5, default_return=None, sleep_time=0):
    def _first(func):
        def _next(*args, **kwargs):
            nonlocal count
            count -= 1
            try:
                result = func(*args, **kwargs)
                if result.status_code != 200:
                    print(result.url)
                    print(result.status_code)
                    print(result.content.decode())
                    time.sleep(sleep_time)
                    result = _next(*args, **kwargs) if count > 0 else default_return
            except Exception as e:
                print('func: {}, error: {}'.format(func.__name__, e))
                time.sleep(sleep_time)
                result = _next(*args, **kwargs) if count > 0 else default_return
            return result

        return _next

    return _first


@retry(sleep_time=1)
def base_req(url_, method='GET', **kwargs):
    if not url_.startswith('http'):
        url_ = 'http://www.gsxt.gov.cn' + url_
    time.sleep(.2)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Cookie': '__jsluid_h=21d96c5816e9ec316c9616ff2542c9dd; __jsl_clearance=1573024491.899|0|l%2BkdW3s0ty5QXG3Et'
                  '%2FpOS6OseR4%3D; UM_distinctid=16e3f90ee026e-005fb45c7eb25d-3a65460c-1fa400-16e3f90ee03287; CNZZD'
                  'ATA1261033118=1199770926-1573023298-http%253A%252F%252Fwww.gsxt.gov.cn%252F%7C1573023298; Hm_lvt_d'
                  '7682ab43891c68a00de46e9ce5b76aa=1572860591,1573024631; Hm_lpvt_d7682ab43891c68a00de46e9ce5b76aa=15'
                  '73024637; gsxtBrowseHistory1=%0FS%04%06%1D%04%1D%10SNS%24%26%3B%22%3D%3A71%3A%3B01%3A%219ADDDDDADD'
                  'EDADEDEDDDFGFF%40SXS%11%1A%00%1A%15%19%11SNS%E9%86%B9%E5%BB%B2%E5%B9%B6%E6%B9%A9%E5%8D%A3%E5%8D%8E'
                  '%E6%9C%84%E5%B1%88%E6%81%A9%E8%88%8E%E6%9D%9B%E5%9E%8D%E8%AF%99%E6%9D%BD%E9%98%A4%E5%84%98%E5%8E%8C'
                  'SXS%11%1A%00%00%0D%04%11SNEEGDXS%02%1D%07%1D%00%00%1D%19%11SNEACGDFBCLMDDM%09; JSESSIONID=1367A6C6F'
                  'F523F607795C5DB944C71D5-n1:11; tlb_cookie=S172.16.12.68'
        # __jsluid_h=21d96c5816e9ec316c9616ff2542c9dd; __jsl_clearance=1573024491.899|0|l%2BkdW3s0ty5QXG3Et%2FpOS6OseR4%3D
    }
    if 'headers' in kwargs:
        kwargs['headers'].update(headers)
    else:
        kwargs['headers'] = headers
    return requests.session().request(method, url_, verify=False, **kwargs)


def get(url_, **kwargs):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Upgrade-Insecure-Requests': '1',
        'Referer': url_,
    }
    return base_req(url_, headers=headers, **kwargs)


def post(url_, referer_url='', **kwargs):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'http://www.gsxt.gov.cn',
        'Referer': referer_url,
        'X-Requested-With': 'XMLHttpRequest'
    }
    data = {'draw': '1', 'start': '0', 'length': '5'}
    return base_req(url_, method='POST', headers=headers, data=data, **kwargs)


def page_detail(resp):
    result = resp.content.decode()
    post_url = re.findall('var entBusExcepUrl = "(.*?)"', result)
    tree = HTML(result)
    company_name = tree.xpath('//div[@class="companyName"]/h1/text()')[0].strip()
    company_status = tree.xpath('//div[@class="companyName"]/span[@class="companyStatus"]/text()')[0].strip()
    company_msg = tree.xpath('//div[@class="companyName"]/div[@class="msgTitle"]/text()')[0].strip()
    company_detail = tree.xpath('//div[@class="companyDetail clearfix"]/span/span/text()')
    company_code, user, organ, date = [i.strip() for i in company_detail]
    data = {'post_url': post_url, '公司名称': company_name, '公司状态': company_status, '备注': company_msg,
            '统一社会信用代码': company_code, '法定代表人': user, '登记机关': organ, '成立日期': date}
    return data


def abnormal_detail(resp):
    result = resp.content.decode()
    result = json.loads(result)
    total_page = result.get('totalPage')
    data = result.get('data')
    info = {'abntime': '列入日期', 'decOrg_CN': '作出决定机关(列入)', 'reDecOrg_CN': '作出决定机关(移出)',
            'remDate': '移出日期', 'remExcpRes_CN': '移出经营异常名录原因', 'speCause_CN': '列入经营异常名录原因'}
    data_list = [{v: each.get(k) for k, v in info.items()} for each in data]
    return {'total_page': total_page, 'data_list': data_list}


def main():
    url_path = r'C:\Users\17337\houszhou\data\SpiderData\重庆两江信用\page_list.txt'
    url_list = BaseCode().get_data_from_txt(url_path)
    for url in url_list:
        get_resp = get(url)
        if get_resp:
            data = page_detail(get_resp)
            post_url = data.get('post_url')
            post_resp = post(post_url, referer_url=url)
            post_data = abnormal_detail(post_resp)
            print(data)
            print(post_data)
        break


def test():
    # p = get_proxies()
    # url = 'http://www.gsxt.gov.cn/%7B1543C01B7D6261C98E5507185FBEE3855E97602738F110C7445B3DE62F23895200C928FF7C63943C' \
    #       '85E34BF20557A0BF5F04E0AB2B8A9DFE5FBBF89B3A95FDDEEDDEEDDEEDCEFDCEC1F2D1E2EDDED1E2D1E2EBC9C0C951D61B464A26A0' \
    #       'E7065BB9EB8DCA3837381A299FC268D12364481E593F164BE158EE19B108FF366B2CDED1E2D1E2D1E2-1573005108815%7D'
    # req = get(url)
    # print(req.status_code)
    # page_detail(req)
    # new = base_req(url, cookies=cook, headers={})
    # print(new.status_code)
    # print(new.content.decode())
    # print(new.cookies)
    post_url = 'http://www.gsxt.gov.cn/%7B575B82033F7A23D1CC4D45001DA6A19D1C8F223F7AE952DF06435EE5E2D5278AB3C5C9D4E8AD1716A8B96398D5EC17A9B0897287B5CCA5CCA5CCA5DCB5DCBED7AEFBA8C194F69FE6B58B495201631B6200DD4A4D1B2D-1573008154988%7D'
    from_url = 'http://www.gsxt.gov.cn/%7B3D31E869551049BBA6272F6A77CCCBF776E54855108338B56C2915940751A12028BB008D5411BC4EAD9163802D2588CD7776C8D903F8B58C77C9D0E912E7D5ACC5ACC5ACC5BCD5BCDEB7CE9BC8A1F496FF86D5EB293261037B0260BD2A2D7B4D918C37308880BCA1095A0F7625C9CE3EDD75681E120F334047B754B815E704A93A3D2088DDB4DDB4DDB4-1573005315961%7D'
    req = post(post_url, referer_url=from_url)
    print(req.status_code)
    print(req.content.decode())
    print(abnormal_detail(req))


if __name__ == '__main__':
    main()
