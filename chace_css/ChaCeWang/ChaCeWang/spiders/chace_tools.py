import copy
import json
import os
import time
from collections import defaultdict

import pandas as pd
import requests
import scrapy
from fontTools.ttLib import TTFont

from chace_css.ChaCeWang.ChaCeWang.settings import FONT_FILE, FONT_LIST, PROJECT_TYPE, CITY, CITY_PATH, HEADERS, COOKIES
from tools.base_code import BaseCode as BCode, Append2Excel as AEexcel


class SpiderCha:
    def __init__(self):
        self.project_type = PROJECT_TYPE
        self.city_list = BCode().excel2json(CITY_PATH)
        self.city = CITY
        self.change_font = self.get_font()

    def page_detail(self, tree: scrapy.http.Response):
        name = tree.xpath('//div[@class="detail-title"]/p/text()').extract_first()
        department = tree.xpath('//*[@id="titleInfo"]/span[@class="detail-type"]/span/text()').extract_first()
        time_map = tree.xpath('//*[@id="titleInfo"]/span[@class="detail-time"]/text()').extract()  # 无需替换
        category = tree.xpath('//ul[@class="list-unstyleds ccw-font-style"]/li/text()').extract()  # 产业类别
        condition = self.xpath_string(tree, "申报条件")
        vigor = self.xpath_string(tree, "支持力度")
        material = self.xpath_string(tree, "申报材料")
        source = self.xpath_string(tree, "项目来源", is_change=False)  # 无需替换
        analysis = self.xpath_string(tree, "项目分析")
        system = self.xpath_string(tree, "申报系统", is_change=False)  # 无需替换
        result = {'项目名称': self.change(name), '受理部门': self.change(department),
                  '申报时间': ''.join(time_map).strip(), '产业类别': [self.change(i) for i in category],
                  '申报条件': condition, '支持力度': vigor, '申报材料': material, '项目来源': source,
                  '项目分析': analysis, '申报系统': system, '链接': tree.url}
        return result

    def xpath_string(self, tree, xpath_name, is_change=True):
        xpath_str = '//div[@class="detail-content project-detail"]/div/p[contains(text(), "{}")]/following-sibling::p'
        con_list = tree.xpath(xpath_str.format(xpath_name))
        result_str = '\n'.join([each.xpath('string(.)').extract_first() for each in con_list])
        return self.change(result_str) if is_change else result_str

    def change(self, detail):
        return ''.join([self.change_font.get(each, each) for each in detail]) if detail else ''

    def city_code(self, k):
        return {i.get(k): i for i in self.city_list}

    @staticmethod
    def get_font():
        # 找出字体和字体文件中编码的对应关系,保存为字典
        font_file = TTFont(FONT_FILE)
        font_dict = dict(zip(font_file.getGlyphOrder(), FONT_LIST))
        return {chr(k): font_dict[v] for k, v in font_file['cmap'].getBestCmap().items()}


def to_one(dir_path, save_path):
    data_dict = defaultdict(list)
    for excel in os.listdir(dir_path):
        print(excel)
        excel_path = os.path.join(dir_path, excel)
        for each in BCode().get_data_from_json(excel_path):
            data_dict[each.get('链接')].append(each)
    save_list = []
    for k, v in data_dict.items():
        new_ = list_value(v)
        if new_:
            new_json = copy.deepcopy(v[0])
            new_json.update(new_)
            save_list.append(new_json)
    BCode().json2excel(all_json=save_list, save_path=save_path, index=False)


def list_value(self_list):
    # need = {'股权资助', '事前资助', '科技奖励', '配套资助', '事后资助', '研发资助', '产业化', '招商引资', '创新载体',
    #         '人才认定与资助', '产业基金', '产业联盟', '新兴产业', '传统产业', '高新技术企业', '总部企业', '大型企业'}
    re_dict = {'项目类别': set(), '城市': set(), '地区': defaultdict(set)}
    for item in self_list:
        city = item.get('城市')
        re_dict['项目类别'].add(item.get('项目类别'))
        re_dict['城市'].add(city)
        re_dict['地区'][city].add(item.get('地区'))
    return {'项目类别': list(re_dict['项目类别']), '城市': list(re_dict['城市']),
            '地区': {k: list(v) for k, v in re_dict['地区'].items()}}


def clean_type(excel_path, save_path):
    need = {'股权资助', '事前资助', '科技奖励', '配套资助', '事后资助', '研发资助', '产业化', '招商引资', '创新载体',
            '人才认定与资助', '产业基金', '产业联盟', '新兴产业', '传统产业', '高新技术企业', '总部企业', '大型企业'}
    new_json = []
    for item in BCode().excel2json(excel_path):
        new_type = [i for i in json.loads(item.get('项目类别').replace('\'', '\"')) if i in need]
        if new_type:
            new_item = item.copy()
            new_item['项目类别'] = new_type
            new_json.append(new_item)
    # print(len(new_json))
    BCode().json2excel(new_json, save_path, index=False)


class Department:
    def __init__(self):
        self.excel = AEexcel(r'C:\Users\17337\houszhou\data\SpiderData\查策网\city_department_惠州.xlsx')
        self._area = BCode().excel2json(r'C:\Users\17337\houszhou\data\SpiderData\查策网\city_area.xlsx')

    def main(self):
        for item in self._area:
            print(item)
            area_uid = item.get('area')
            department_list = [i for i in self.get(area_uid)]
            save = item.copy()
            save['部门'] = department_list
            print(save)
            self.excel.add(save)
            time.sleep(1)

    def get(self, uid):
        result = self._req(uid).content.decode()
        for item in json.loads(result):
            full_name = item.get('FullName')
            yield full_name

    @staticmethod
    def _req(uid):
        url = 'http://www.chacewang.com/ProjectSearch/GetDiqu?dictionaryCode={}'.format(uid)
        return requests.get(url, headers=HEADERS, cookies=COOKIES, verify=False)

    def test(self):
        for each in self.get('RegisterArea_ZXS_Beijing_MiYunXian'):
            print(each)


def no_type(all_path, type_path, save_path):
    all_data = pd.read_excel(all_path)
    type_data = pd.read_excel(type_path)
    all_set = set(all_data.get('链接'))
    type_set = set(type_data.get('链接'))
    no_set = all_set - type_set
    new = [item for item in all_data.to_dict(orient='records') if item.get('链接') in no_set]
    print(len(new))
    BCode.json2excel(new, save_path)
    # print(new)


if __name__ == '__main__':
    to_one(r'C:\Users\17337\houszhou\data\SpiderData\查策网\1107惠州\done',
           r'C:\Users\17337\houszhou\data\SpiderData\查策网\1107惠州\查策网_深圳惠州_1108_合并去重.xlsx')
    # department = Department()
    # department.main()
    # no_type(r'C:\Users\17337\houszhou\data\SpiderData\查策网\futian\查策网_深圳_1105_all.xlsx',
    #         r'C:\Users\17337\houszhou\data\SpiderData\查策网\futian\查策网_深圳_1105_项目类别.xlsx',
    #         r'C:\Users\17337\houszhou\data\SpiderData\查策网\futian\查策网_深圳_1105_无项目类别_1631.xlsx')
