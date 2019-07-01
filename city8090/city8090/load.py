import requests
import json


def base_req(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
    data = {'pageNumber': '3', 'maxPageItems': '100'}
    req_data = requests.post(url, headers=headers, data=data, verify=False)
    return req_data


def post_test():
    url = 'http://pnr.sz.gov.cn/d-ghweb/placename/name/web/placeNameAction.go?method=listPnPlaceNames'
    data = base_req(url)
    print(data.content)
    data_str = data.content.decode('gbk')
    data = json.loads(data_str.strip())
    for item in data.get('rows'):
        print(item)


if __name__ == '__main__':
    url = 'http://samr.cfda.gov.cn/WS01/CL1664/'
    data = requests.get(url)
    print(data.content.decode())
