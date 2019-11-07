import json
import time

from lxml.etree import HTML
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from tools.base_code import BaseCode


class Gsxt:
    def __init__(self):
        date = '国家企业信用信息_1107_0955'
        self.sleep_time = 100
        self.path = r'C:\Users\17337\houszhou\data\SpiderData\重庆两江信用\{}.json'.format(date)
        self.error_path = r'C:\Users\17337\houszhou\data\SpiderData\重庆两江信用\{}_error.txt'.format(date)
        self.url_path = r'C:\Users\17337\houszhou\data\SpiderData\重庆两江信用\国家企业信用信息_1106_1832_error.txt'
        self.url_list = BaseCode().get_data_from_txt(self.url_path)
        self.file = open(self.path, 'a', encoding='utf8')
        self.error = open(self.error_path, 'a', encoding='utf8')

    def __del__(self):
        self.file.close()
        self.error.close()

    def main(self):
        for url_ in self.url_list:
            url = url_ if 'http' in url_ else 'http://www.gsxt.gov.cn' + url_
            try:
                self.get(url)
            except Exception as e:
                print('error: ', url)
                print(e)
                self.error.write(url + '\n')
                self.error.flush()
            time.sleep(self.sleep_time)

    def get(self, url):
        print(url)
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 60)
        self.browser.get(url)
        self.wait.until(EC.presence_of_element_located((By.ID, 'abnormalInSubData0')))
        self.page_detail()
        self.browser.close()

    def page_detail(self):
        result = self.browser.page_source
        tree = HTML(result)
        company_name = from_xpath(tree, '//div[@class="companyName"]/h1/text()')
        company_status = from_xpath(tree, '//div[@class="companyName"]/span[@class="companyStatus"]/text()')
        company_msg = from_xpath(tree, '//div[@class="companyName"]/div[@class="msgTitle"]/text()')
        company_detail = tree.xpath('//div[@class="companyDetail clearfix"]/span/span/text()')
        company_code, user, *organ, date = [i.strip() for i in company_detail]
        organ_name = '注销原因' if '注销' in company_status else "登记机关"
        table_tree = tree.xpath('//tr[@class="odd"]')
        table_xpath = {'列入日期': 'td[3]/text()', '作出决定机关(列入)': 'td[4]/text()', '序号': 'td[1]/text()',
                       '列入经营异常名录原因': 'td[2]/div/span/text()', '移出日期': 'td[6]/text()',
                       '作出决定机关(移出)': 'td[7]/text()', '移出经营异常名录原因': 'td[5]/div/span/text()'}
        company_data = {'公司名称': company_name, '公司状态': company_status, '备注': company_msg,
                        '记录次数': len(table_tree), '统一社会信用代码': company_code, '法定代表人': user,
                        organ_name: organ[0] if organ else "", '成立日期': date}
        for item in table_tree:
            table_data = {k: from_xpath(item, v) for k, v in table_xpath.items()}
            table_data.update(company_data)
            print(table_data)
            self.write(table_data)

    def write(self, data=None):
        self.file.write(json.dumps(dict(data), ensure_ascii=False) + '\n')
        self.file.flush()

    def test(self):
        url = 'http://www.gsxt.gov.cn/%7BA7F072A8CFD1D37A3CE6B5ABED0D5136EC24D2948A42A274F6E88F559D903BE1B27A9A4CCED0268F3750F941B7E4120CEDB7521899392F4DED084A2888264F6D5F6D5F6D5F7D4F7D4476545A52606EF7C585B78EBC9EDE9EA785BC3AF6AAA7CA4D0BEBB754076026D5DBD5F6C4732F843CCF89A4F3B5D2FAA60DB502F45DE513DB87C1323C0E3C0E3C0E-1573005108814%7D'
        self.get(url)
        time.sleep(20)


def from_xpath(data, re_xpath):
    result = data.xpath(re_xpath)
    return result[0].strip() if result else ''


if __name__ == '__main__':
    gs = Gsxt()
    gs.main()
