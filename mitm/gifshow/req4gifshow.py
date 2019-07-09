import requests


def base_req():
    url = 'http://103.107.217.65/rest/n/feed/hot?isp=CMCC&mod=vivo%28vivo%20y23l%29&lon=116.41025&country_code=cn&kpf=ANDROID_PHONE&extId=e8e26ebe7f2bded23b9ae3eed30a903a&did=ANDROID_0cfc58736cb6c8c6&kpn=KUAISHOU&net=WIFI&app=0&oc=MYAPP%2C1&ud=1104788342&hotfix_ver=&c=MYAPP%2C1&sys=ANDROID_5.1.1&appver=6.1.0.8039&ftt=&language=zh-cn&iuid=&lat=39.916411&did_gt=1562503556381&ver=6.1&max_memory=192'
    data = {
        'type': '7',
        'page': '6',
        'coldStart': 'false',
        'count': '20',
        'pv': 'false',
        'id': '14',
        'refreshTimes': '4',
        'pcursor': '1',
        'source': '1',
        'needInterestTag': 'false',
        '__NStokensig': '8e02d5d545d8417d2499cfdb5b13fe7ee1aca6a432eea504eca04c5aaaf4b39a',
        'token': '6198aa09169b4a75b072ed6fb1179311-1104788342',
        'client_key': '3c2cd3f3',
        'os': 'android',
        'sig': '67da53d853656ee68efd82cb2a4195f6',
    }
    headers = {
        'Cookie': 'token=6198aa09169b4a75b072ed6fb1179311-1104788342',
        'X-REQUESTID': '165179',
        'User-Agent': 'kwai-android',
        'Connection': 'keep-alive',
        'Accept-Language': 'zh-cn',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': '305',
        'Host': '103.107.217.65',
        'Accept-Encoding': 'gzip'
    }
    req_data = requests.post(url, data, headers=headers, verify=False)
    return req_data


if __name__ == '__main__':
    d = base_req()
    print(d.content.decode())
