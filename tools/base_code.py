import xlrd
import openpyxl
import json
import os
from collections import defaultdict

import pandas as pd


class BaseCode(object):

    @staticmethod
    def count_list_items(data_list):
        '''
        统计一个列表的元素出现的次数
        :param data_list: 待解析的list
        :return: {1:[a, b], 2:[c], 3:[d,e]}
        '''
        data_json = defaultdict(lambda: 0)
        new_v = defaultdict(lambda: [])
        for item in data_list:
            data_json[item] += 1
        for k, v in data_json.items():
            new_v[v].append(k)
        return dict(new_v)

    def get_file_from_dir(self, dir_path, file_type="wav"):
        '''
        获取一个文件夹下指定文件后缀的所有的文件
        :param dir_path: 待解析的文件夹
        :param file_type: 指定获取的文件类型，类型不限时：file_type=""
        :return: file list
        '''
        return self._get_file_from_dir(dir_path, [], file_type)

    def _get_file_from_dir(self, dir_path, file_list, file_type):
        for item in os.listdir(dir_path):
            now_path = os.path.join(dir_path, item)
            if os.path.isfile(now_path) and now_path.endswith(file_type):
                file_list.append(now_path)
            elif os.path.isdir(now_path):
                self._get_file_from_dir(now_path, file_list, file_type)
        return file_list

    @staticmethod
    def get_data_from_json(json_file, encoding="utf8"):
        with open(json_file, "r", encoding=encoding)as f:
            return [json.loads(line.strip()) for line in f]

    @staticmethod
    def get_data_from_txt(txt_file, encoding="utf8"):
        with open(txt_file, "r", encoding=encoding)as f:
            return [line.strip() for line in f]

    @staticmethod
    def cut_list_by_count(list_in, e_count):
        num = len(list_in) // e_count
        num = num if len(list_in) % e_count == 0 else num + 1
        return [list_in[i * e_count:(i + 1) * e_count] for i in range(num)]

    @staticmethod
    def json2excel(all_json, save_path, index=True):
        df = pd.DataFrame(all_json)
        df.to_excel(save_path, index=index)

    @staticmethod
    def excel2json(excel_path, orient='records'):
        df = pd.read_excel(excel_path)
        return df.to_dict(orient=orient)

    @staticmethod
    def str2json(json_str, replace=False):
        if replace:
            json_str = json_str.replace('\'', '\"')
        return json.loads(json_str)


class Append2Excel:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.csv_path = self.excel_path.replace('.xlsx', '.csv')
        self._need_head = True

    def add(self, data: list):
        df = pd.DataFrame(data)
        df.to_csv(self.csv_path, mode='a', encoding='utf8', index=False, header=self._need_head)
        self._need_head = False

    @property
    def need_head(self):
        return self._need_head

    @need_head.setter
    def need_head(self, need):
        if isinstance(need, bool):
            self._need_head = need
        else:
            print('need 类型必须为bool')

    def __del__(self):
        if os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path)
            df.to_excel(self.excel_path, index=False)


def test():
    ae = Append2Excel(r'C:\Users\17337\houszhou\data\SpiderData\test_excel.xlsx')
    ae.need_head = False
    print(ae.need_head)


if __name__ == '__main__':
    bc = BaseCode()
    test()
