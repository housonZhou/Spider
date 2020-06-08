# uncompyle6 version 3.6.6
# Python bytecode 3.7 (3394)
# Decompiled from: Python 3.6.8 (tags/v3.6.8:3c6b436a57, Dec 24 2018, 00:16:47) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: D://外发//svn//Policy//extractdata\extractdata\extractdata\ZoneInfo.py
# Compiled at: 2020-04-16 20:48:09
# Size of source mod 2**32: 2133 bytes
import os

import pandas as pd

from db_lib.to_db.settings import FILE_EXCEL

info = pd.read_excel(os.path.join(FILE_EXCEL, 'china_area_info.xlsx'))
city_info = info[info.AREA_LEVEL.str.contains('C', na=False)]


class SubRegion:
    City = {}
    for i in range(len(city_info)):
        if type(city_info.iloc[i]['MUNICIPAL_NAME']) != float:
            if city_info.iloc[i]['MUNICIPAL_NAME'] in City:
                City[city_info.iloc[i]['MUNICIPAL_NAME']].append(city_info.iloc[i]['AREA_NAME'])
            else:
                City.update({city_info.iloc[i]['MUNICIPAL_NAME']: [city_info.iloc[i]['AREA_NAME']]})

    for line in City:
        City[line].append(line)


def if_nan(item):
    if item == '   ':
        item = ''
    else:
        item = item
    return item


Area = []
for i in range(len(info)):
    Area.append(info.iloc[i]['AREA_NAME'])

Level = []
for i in range(len(city_info)):
    if city_info.iloc[i]['PROVINCIAL_NAME'] not in ('北京市', '上海市', '天津市', '重庆市'):
        Level.append([if_nan(city_info.iloc[i]['PROVINCIAL_NAME']), if_nan(city_info.iloc[i]['MUNICIPAL_NAME']),
         if_nan(city_info.iloc[i]['AREA_NAME'])])
    else:
        Level.append(['', if_nan(city_info.iloc[i]['PROVINCIAL_NAME']), if_nan(city_info.iloc[i]['AREA_NAME'])])

group_info = pd.read_excel(os.path.join(FILE_EXCEL, 'human_group_base.xlsx'))
Group = []
for i in range(len(group_info)):
    Group.append([group_info.iloc[i]['KEY_NAME'], group_info.iloc[i]['KEY']])

profession_info = pd.read_excel(os.path.join(FILE_EXCEL, 'result.xls'))
Profession = []
for i in range(len(group_info)):
    try:
        Profession.append([profession_info.iloc[i]['type'], profession_info.iloc[i]['words'].split(',')])
    except:
        pass