# uncompyle6 version 3.6.6
# Python bytecode 3.7 (3394)
# Decompiled from: Python 3.6.8 (tags/v3.6.8:3c6b436a57, Dec 24 2018, 00:16:47) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: D://外发//svn//Policy//extractdata\extractdata\extractdata\ExtratcGroup.py
# Compiled at: 2020-04-20 14:35:32
# Size of source mod 2**32: 4001 bytes
import json

from db_lib.extractdata import ExtratcDept
from db_lib.extractdata.ZoneInfo import Group, Profession
from db_lib.extractdata.app import Ind


class Model:
    def __init__(self, source, website, title, content):
        self.source = str(source)
        self.website = str(website)
        self.title = str(title)
        self.content = str(content)
        self.text = self.title + self.content
        self.Region = ExtratcDept.REGION(source, website, title)
        self.dept = self.Region.Dept()

    def get_group(self):
        # 对象
        result = []
        text = self.text
        for item in Group:
            if item[0] in text and item[1] not in result:
                result.append(item[1])
        return result

    def get_profession(self):
        # 行业
        result = []
        text = self.text
        for item in Profession:
            for pro in item[1]:
                if pro in text and item[0] not in result:
                    result.append(item[0])

        return result

    def get_industry(self):
        # 产业
        res = Ind.predict(self.title, self.content)
        industry = [item['name'] for item in res]
        return industry

    def get_region(self):
        # 地区
        region = self.dept[0]
        return region

    def get_level(self):
        # 获取政策层级
        level = self.dept[1]
        return level

    def get_dept(self):
        # 获取部门
        level = self.dept[2]
        return level

    def get_all(self, string=False):
        industry = self.get_industry()
        profession = self.get_profession()
        group = self.get_group()
        return {'level': self.get_level(), 'region': self.get_region(),
                'industry': json.dumps(industry, ensure_ascii=False) if string else industry,
                'profession': json.dumps(profession, ensure_ascii=False) if string else profession,
                'group': json.dumps(group, ensure_ascii=False) if string else group,
                'dept': self.get_dept()}
