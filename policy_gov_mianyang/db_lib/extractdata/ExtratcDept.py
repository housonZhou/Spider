# uncompyle6 version 3.6.6
# Python bytecode 3.7 (3394)
# Decompiled from: Python 3.6.8 (tags/v3.6.8:3c6b436a57, Dec 24 2018, 00:16:47) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: D://外发//svn//Policy//extractdata\extractdata\extractdata\ExtratcDept.py
# Compiled at: 2020-04-20 14:56:22
# Size of source mod 2**32: 8057 bytes
import re

import jieba as jb
import jieba.analyse

from db_lib.extractdata.ZoneInfo import SubRegion, Area, Level
from db_lib.extractdata.constant import Region, Dept

jb_suggest = [
    ('广州', '市政府'), ('深圳', '市政府'), ('深圳', '特区'), ('深圳', '机场'), ('上海', '海关'),
    ('上海市', '浦东新区'), ('百色', '地区'), ('喀什', '地区'), ('新疆', '地区'), ('广州', '地区'),
    ('西藏', '自治区'), ('广州', '白云机场'), ('香港', '市民'), ('武汉', '三镇'), '雷神山', ('湖北', '日报'),
    '长安剑']
for word in jb_suggest:
    jb.suggest_freq(word, tune=True)

SR = {}
for line in SubRegion.City.items():
    for item in line[1]:
        SR.update({item: line[0]})

DeptCountry = {}
for line in Dept.Country.items():
    for item in line[1]:
        DeptCountry.update({item: line[0]})

DeptProv = {}
for line in Dept.Province.items():
    for item in line[1]:
        DeptProv.update({item: line[0]})

DeptCity = {}
for line in Dept.City.items():
    for item in line[1]:
        DeptCity.update({item: line[0]})


class REGION:

    def __init__(self, source, website, title):
        self.source = source
        self.website = website
        self.title = title

    def KnownExtract(self, text, region, n):
        for City in Region.City:
            if City in text:
                region = [
                    City]
                n = 1
                return (
                    region, n)

        for Province in Region.Province:
            if Province in text:
                region = [
                    Province]
                n = 2
                return (
                    region, n)

        return (
            region, n)

    def SubRegionExtract(self, region, SR):
        for line in SR:
            if region == line:
                region = SR[line]
                return region

    def ReadRegionName(self, region, Area):
        for area in Area:
            if region[0] in area:
                region[0] = area
                return region

    def RegionExtract(self, text):
        n = 0
        region = []
        try:
            a = re.search('^\\[.*?\\]', text)
            ProR = text[a.span()[0] + 1:a.span()[1] - 1]
        except:
            ProR = ''

        if ProR:
            for line in Area:
                if ProR in line:
                    region.append(line)
                    n = 0
                    break

        else:
            for line in Area:
                if line in text:
                    region.append(line)

        if len(region) > 1:
            final_rerion = region[(-1)]
        else:
            final_rerion = region
        title_region = jb.analyse.extract_tags(text, topK=1, allowPOS=['ns'])
        if final_rerion:
            return (final_rerion, n)
        if title_region:
            region = self.ReadRegionName(title_region, Area)
            return (
                region, n)

    def RegionMatch(self):
        """
        source的优先级为1(数字为3) website优先级为2（数字为2）
        如果source的机构层级比解析出来的website层级高，保留以source层级为主
        如果source的机构层级比解析出来的website底，再根据题目解析，判断保留高还是低
        如果source的机构层级比解析出来的website低，但题目没有提，保留Website
        :param line:
        :return:
        """
        region = []
        try:
            if '国' in self.source:
                SouR = [
                    '中国']
                n1 = 3
            else:
                SouR, n1 = self.RegionExtract(self.source)
        except:
            SouR = ([],)
            n1 = 0

        try:
            if '国' in self.website:
                WebR = [
                    '中国']
                n2 = 3
            else:
                WebR, n2 = self.RegionExtract(self.website)
        except:
            WebR = ([],)
            n2 = 0

        try:
            TitR, n3 = self.RegionExtract(self.title)
        except:
            TitR = []
            n3 = 0

        if n1 > n2:
            region = SouR
        elif n1 < n2:
            if n1 == 0:
                region = WebR
            elif TitR:
                region = TitR
            else:
                region = WebR
        elif SouR != ([],):
            region = SouR
        elif WebR != ([],):
            region = WebR
        elif TitR != ([],):
            region = TitR
        elif n1 == n2:
            region = SouR
        return region

    def RegionLevelSta(self, line):
        if line:
            region = line[0]
            level = ''
            real_region = ''
            for municipal in Level:
                if region == municipal[0]:
                    real_region = municipal[0]
                    level = '省级'
                    break
                else:
                    if region == municipal[1]:
                        real_region = municipal[1]
                        level = '市级'
                        break

            if not real_region:
                if region == '中华人民共和国' or region == '中国':
                    real_region = '全国'
                    level = '国家级'
        else:
            real_region = '全国'
            level = '国家级'
        return (real_region, level)

    def DeptExtract(self, DeptWords):
        Dept = ''
        try:
            for a in DeptWords.keys():
                if a in self.source:
                    Dept = DeptWords[a]
                    return Dept

        except:
            pass

        if not Dept:
            try:
                for a in DeptWords.keys():
                    if a in self.website:
                        Dept = DeptWords[a]
                        return Dept

            except:
                pass

        if not Dept:
            try:
                for a in DeptWords.keys():
                    if a in self.title:
                        Dept = DeptWords[a]
                        return Dept

            except:
                pass

        return Dept

    def GetLevel(self, real_region, Level):
        region_final = ''
        for line in Level:
            for i in range(len(line)):
                if real_region == line[i]:
                    region_final = '-'.join(line[0:i + 1])
                    return region_final

    def DeptMatch(self, level, real_region):
        if level == '国家级':
            Dept_ = self.DeptExtract(DeptCountry)
            region_final = real_region
        elif level == '省级':
            b = self.DeptExtract(DeptProv)
            region_final = real_region
            if b:
                Dept_ = real_region + b
            else:
                Dept_ = ''
        elif level == '市级':
            b = self.DeptExtract(DeptCity)
            region_final = self.GetLevel(real_region, Level)
            if b:
                Dept_ = real_region + b
            else:
                Dept_ = ''
        elif level == '区县级':
            b = self.DeptExtract(DeptCity)
            region_final = self.GetLevel(real_region, Level)
            if b:
                Dept_ = self.SubRegionExtract(real_region, SR) + real_region + b
            else:
                Dept_ = ''
        else:
            Dept_ = ''
            region_final = real_region
        return (Dept_, region_final)

    def Dept(self):
        real_region, level = self.RegionLevelSta(self.RegionMatch())
        dept, region = self.DeptMatch(level, real_region)
        return (
            region, level, dept)
