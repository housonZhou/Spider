import requests
import json


def base_req(url):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': 'https://www.creditchina.gov.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
        'Referer': 'https://www.creditchina.gov.cn/xinyongfuwu/shouxinhongmingdan/',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    resp = requests.get(url, verify=False, headers=headers)
    return resp


def main():
    """
    守信激励查询
    return {'page': 1, 'total': 500, 'totalSize': 5, 'list': []}
    keyword  page pageSize
    GET /private-api/typeNameAndCountSearch?keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA&searchState=2&page=1&pageSize=20&type=%E5%AE%88%E4%BF%A1%E6%BF%80%E5%8A%B1&entityType=1%2C4%2C5%2C6%2C7%2C8 HTTP/1.1
        /private-api/typeNameAndCountSearch?keyword=重庆两江新区&searchState=2&page=1&pageSize=10&type=守信激励&entityType=1,4,5,6,7,8
Host: public.creditchina.gov.cn
Connection: keep-alive
Accept: application/json, text/javascript, */*; q=0.01
Origin: https://www.creditchina.gov.cn
User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36
Referer: https://www.creditchina.gov.cn/xinyongfuwu/shouxinhongmingdan/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9

失信惩戒
GET /private-api/typeNameAndCountSearch?keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA&searchState=2&page=1&pageSize=10&type=%E5%A4%B1%E4%BF%A1%E6%83%A9%E6%88%92&entityType=1%2C4%2C5%2C6%2C7%2C8 HTTP/1.1
    /private-api/typeNameAndCountSearch?keyword=重庆两江新区&searchState=2&page=1&pageSize=10&type=失信惩戒&entityType=1,4,5,6,7,8
Host: public.creditchina.gov.cn
Connection: keep-alive
Accept: application/json, text/javascript, */*; q=0.01
Origin: https://www.creditchina.gov.cn
User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36
Referer: https://www.creditchina.gov.cn/xinyongfuwu/shixinheimingdan/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9

行政处罚
https://public.creditchina.gov.cn/private-api/typeNameAndCountSearch?keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA&type=%E8%A1%8C%E6%94%BF%E5%A4%84%E7%BD%9A&searchState=2&entityType=1%2C2%2C3%2C7&page=1&pageSize=10
https://public.creditchina.gov.cn/private-api/typeNameAndCountSearch?keyword=重庆两江新区&type=行政处罚&searchState=2&entityType=1,2,3,7&page=1&pageSize=10
行政许可
https://public.creditchina.gov.cn/private-api/typeNameAndCountSearch?keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA&type=%E8%A1%8C%E6%94%BF%E8%AE%B8%E5%8F%AF&searchState=2&entityType=1%2C2%2C3%2C7&page=1&pageSize=10
https://public.creditchina.gov.cn/private-api/typeNameAndCountSearch?keyword=重庆两江新区&type=行政许可&searchState=2&entityType=1,2,3,7&page=1&pageSize=10

基本信息：
/private-api/getTyshxydmDetailsContent?keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA%E7%BD%AE%E4%B8%9A%E5%8F%91%E5%B1%95%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8&scenes=defaultscenario&entityType=1&searchState=1

行政许可
https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=%E8%A1%8C%E6%94%BF%E8%AE%B8%E5%8F%AF&searchState=1&entityType=1&scenes=defaultscenario&keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA%E7%BD%AE%E4%B8%9A%E5%8F%91%E5%B1%95%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8&page=1&pageSize=10
https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=行政许可&searchState=1&entityType=1&scenes=defaultscenario&keyword=重庆两江新区置业发展有限公司&page=1&pageSize=10

行政处罚
https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=%E8%A1%8C%E6%94%BF%E5%A4%84%E7%BD%9A&searchState=1&entityType=1&scenes=defaultscenario&keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA%E7%BD%AE%E4%B8%9A%E5%8F%91%E5%B1%95%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8&page=1&pageSize=10
https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=行政处罚&searchState=1&entityType=1&scenes=defaultscenario&keyword=重庆两江新区置业发展有限公司&page=1&pageSize=10

守信激励
https://public.creditchina.gov.cn/private-api/searchDateCategoryCount?type=%E5%AE%88%E4%BF%A1%E6%BF%80%E5%8A%B1&searchState=1&keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA%E7%BD%AE%E4%B8%9A%E5%8F%91%E5%B1%95%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8&entityType=1
https://public.creditchina.gov.cn/private-api/searchDateCategoryCount?type=守信激励&searchState=1&keyword=重庆两江新区置业发展有限公司&entityType=1
https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=%E5%AE%88%E4%BF%A1%E6%BF%80%E5%8A%B1&searchState=1&entityType=1&scenes=defaultscenario&keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA%E7%BD%AE%E4%B8%9A%E5%8F%91%E5%B1%95%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8&page=1&pageSize=10
https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=守信激励&searchState=1&entityType=1&scenes=defaultscenario&keyword=重庆两江新区置业发展有限公司&page=1&pageSize=10

失信惩戒
https://public.creditchina.gov.cn/private-api/searchDateCategoryCount?type=%E5%A4%B1%E4%BF%A1%E6%83%A9%E6%88%92&searchState=1&keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA%E8%9E%8D%E8%B5%84%E6%8B%85%E4%BF%9D%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8&entityType=1
https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=%E5%A4%B1%E4%BF%A1%E6%83%A9%E6%88%92&searchState=1&entityType=1&scenes=defaultscenario&keyword=%E9%87%8D%E5%BA%86%E4%B8%A4%E6%B1%9F%E6%96%B0%E5%8C%BA%E8%9E%8D%E8%B5%84%E6%8B%85%E4%BF%9D%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8&page=1&pageSize=10
https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=失信惩戒&searchState=1&entityType=1&scenes=defaultscenario&keyword=重庆两江新区融资担保有限公司&page=1&pageSize=10

    """
    url = 'https://public.creditchina.gov.cn/private-api/typeSourceSearch?source=&type=行政许可&searchState=1&entityType=1&scenes=defaultscenario&keyword=重庆两江新区置业发展有限公司&page=1&pageSize=10'
    result = base_req(url)
    print(result.status_code)
    data_str = result.content.decode()
    print(json.loads(data_str).get('data'))
    print(len(json.loads(data_str).get('data').get('list')))


if __name__ == '__main__':
    main()
