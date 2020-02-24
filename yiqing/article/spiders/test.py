import requests
from lxml.etree import HTML


def base_req(url):
    # kwargs = {'verify': False, 'timeout': 10}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        # 'Cookie': 'zh_choose=s; wondersLog_zwdt_sdk=%7B%22persistedTime%22%3A1568700213982%2C%22userId%22%3A%22%22%2C%22superProperties%22%3A%7B%7D%2C%22updatedTime%22%3A1568700246258%2C%22sessionStartTime%22%3A1568700213989%2C%22sessionReferrer%22%3A%22http%3A%2F%2Fzwdt.sh.gov.cn%2FgovPortals%2FzwdtSW%2Findex.jsp%3FshowUrl%3D3%22%2C%22deviceId%22%3A1217576796908587%2C%22LASTEVENT%22%3A%7B%22eventId%22%3A%22%E9%93%BE%E6%8E%A5%E8%AE%BF%E9%97%AE%22%2C%22time%22%3A1568700246256%7D%2C%22sessionUuid%22%3A4855272662121860%2C%22costTime%22%3A%7B%7D%7D; Hm_lvt_77c54f861e1edaa3a8caf6b553ea5b73=1568789575,1568789587; pgv_pvi=4031048704; yd_cookie=ede01ac3-d913-44f2595f6de03e9ff09f7491ccbfc24b335f; _ydclearance=de25aa0f8ed99020945705e3-d87d-4608-9a21-1b305c4b3023-1582092686; AlteonP=AOriAGHbHKyjgjI52HxSKw$$; _gscu_2010802395=82085497drpkqc13; _gscbrs_2010802395=1; _gscs_2010802395=82085497i7gktv13|pv:1; _pk_id.30.0806=857a17170561c2e4.1582085497.1.1582085497.1582085497.; _pk_ses.30.0806=*'
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        # 'Cookie': 'FSSBBIl1UgzbN7N80T=4A2O3pPSr415aJCScCyOx.uTQFpMzlw.M6dUcqXMsVh7uJtRCjkI9TrK83vzOIPovY2AlmRbPv6lfhv18W5A77wVBr8Jf2kr8d2b.AC7eY1movHXevci6.g4q6T4nM5MGDeLqVFjf.c7YWk7DUgnEkjTZ_qa4rc0Yw7DidBHPEYneh.QbsWjavA4jCi0WRme7T5dasTaTMdOmkA92OevH6O8PmwaqI_aoT4lxjT_zUv0tyRcy1JgaEUDZ3lG7lKe67w5EPd7ZdsBVtkKGXoVMidRsaV2QnGiV3deb.vXBvqtEfnUsq0Y6fqEfVzLfD5P0Bi1vaS8WdoV.qpE6bTKgpKKQ; Hm_lpvt_5544783ae3e1427d6972d9e77268f25d=1581950861; FSSBBIl1UgzbN7N80S=uwSu83aBZPhvseKlbyNfwjVGH24mBB4pC4abN1xiaqmfBnOJOfMVXJwXuMzfdzUn; Hm_lvt_5544783ae3e1427d6972d9e77268f25d=1581950861',
}
    response = requests.get(url, headers=headers)
    print(response.status_code)
    con = response.content.decode()
    tree = HTML(con)
    # other = tree.xpath('//div[@class="h1_small"]')
    # print(other)


if __name__ == '__main__':
    url = 'http://jxt.hubei.gov.cn/fbjd/xxgkml/zcwj/zcfg/202002/t20200218_2103657.shtml'
    base_req(url)
    # from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
    # print(urlparse(url).query)
    # data = {'a': 1, 'b': 2}
    # print(urlencode(data))
    # print(parse_qs(urlparse(url).query))