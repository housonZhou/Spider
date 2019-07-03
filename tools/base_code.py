import xlrd
import openpyxl
import json
import os


class BaseCode(object):

    @classmethod
    def count_list_items(cls, data_list):
        '''
        统计一个列表的元素出现的次数
        :param data_list: 待解析的list
        :return: {1:[a, b], 2:[c], 3:[d,e]}
        '''
        data_json = {}
        new_v = {}
        for item in data_list:
            if item in data_json:
                data_json[item] += 1
            else:
                data_json[item] = 1
        for k, v in data_json.items():
            if v in new_v:
                new_v[v].append(k)
            else:
                new_v[v] = [k]
        return new_v

    def _get_file_from_dir(self, dir_path, file_list, file_type):
        for item in os.listdir(dir_path):
            now_path = os.path.join(dir_path, item)
            if os.path.isfile(now_path) and now_path.endswith(file_type):
                file_list.append(now_path)
            elif os.path.isdir(now_path):
                self._get_file_from_dir(now_path, file_list, file_type)
        return file_list

    def get_file_from_dir(self, dir_path, file_type="wav"):
        '''
        获取一个文件夹下指定文件后缀的所有的文件
        :param dir_path: 待解析的文件夹
        :param file_type: 指定获取的文件类型，类型不限时：file_type=""
        :return: file list
        '''
        return self._get_file_from_dir(dir_path, [], file_type)

    @classmethod
    def get_data_from_json(cls, json_file, encoding="utf8"):
        with open(json_file, "r", encoding=encoding)as f:
            return [json.loads(line.strip()) for line in f]

    @classmethod
    def get_data_from_txt(cls, txt_file, encoding="utf8"):
        with open(txt_file, "r", encoding=encoding)as f:
            return [line.strip() for line in f]

    @classmethod
    def generator_list(cls, list_in, count):
        for i in range(count):
            num = (i % len(list_in))
            yield list_in[num]

    def get_data_from_list_by_count(self, list_in, e_count):
        re_list = []
        gn = self.generator_list(list_in, e_count)
        for i in range(e_count):
            re_list.append(next(gn))
        return re_list

    @classmethod
    def from_json_build_excel(cls, all_json, save_path, need_head):
        '''
        将格式化的json数据保存成excel文件
        :param all_json: [{key1:value1, key2:value2}, {key1:value1, key2:value2}, {}, {}...]
        :param save_path: 保存的excel文件路径
        :param need_head: 待保存的json数据的key 如保存所有：[i for i in all_json[0]]
        :return: None
        '''
        wb = openpyxl.Workbook()
        ws = wb.get_active_sheet()
        for i in range(len(need_head)):
            ws.cell(row=1, column=1 + i).value = need_head[i]
        row = 2
        for item in all_json:
            for i in range(len(need_head)):
                ws.cell(row=row, column=1 + i).value = item.get(need_head[i])
            row += 1
        wb.save(save_path)

    def from_all_json_build_excel(self, data_json, save_path):
        self.from_json_build_excel(data_json, save_path, [i for i in data_json[0]])


class Analysis(object):
    """
    读取工具类
    """

    def __init__(self, path="file.xlsx"):
        self.filepath = path

    def open_excel(self, file='file.xlsx'):
        try:
            data = xlrd.open_workbook(file)
            return data
        except Exception:
            print("打开文件异常")

    def excel_table_byindex(self, file, colnameindex=0, by_index=0, start_row=1):
        data = self.open_excel(file)
        table = data.sheets()[by_index]
        nrows = table.nrows  # 行数
        ncols = table.ncols  # 列数
        colnames = table.row_values(colnameindex)  # 某一行数据
        list = []
        for rownum in range(start_row, nrows):
            row = table.row_values(rownum)
            if row:
                app = {}
                for i in range(len(colnames)):
                    app[colnames[i]] = row[i]
                list.append(app)
        return list

    def excel_table_byname(self, file, colnameindex=0, by_name='Sheet1', start_row=1):
        data = self.open_excel(file)
        table = data.sheet_by_name(by_name)
        nrows = table.nrows
        colnames = table.row_values(colnameindex)
        list = []
        for rownum in range(start_row, nrows):
            row = table.row_values(rownum)
            if row:
                app = {}
                for i in range(len(colnames)):
                    app[colnames[i]] = row[i]
                list.append(app)
        return list

    def excel_table_byrow(self, file, by_index=0, start_row=0):
        data = self.open_excel(file)
        table = data.sheets()[by_index]
        list = []
        nrows = table.nrows
        for rownum in range(start_row, nrows):
            row = table.row_values(rownum)
            if row:
                list.append(row)
        return list

    def openpy_excel_bycol(self, file, by_row=0, colnameindex=0):
        wb = openpyxl.load_workbook(file)
        ws = wb.active
        max_rows = ws.max_row
        max_cols = ws.max_column
        list = []
        for col_index in range(colnameindex, max_cols + 1):
            obj_list = []
            for row_index in range(by_row, max_rows + 1):
                obj_list.append(ws.cell(row=row_index, column=col_index).value)
            list.append(obj_list)
        return list


if __name__ == '__main__':
    # pass
    ana = Analysis()
    excel_path = r'C:\Users\17337\Downloads\W020190530357290617892.xls'
    for data in ana.excel_table_byrow(excel_path):
        print(data)
