import scrapy
from fontTools.ttLib import TTFont

from chace_css.ChaCeWang.ChaCeWang.settings import FONT_FILE, FONT_LIST, PROJECT_TYPE, CITY, CITY_PATH
from tools.base_code import BaseCode as BCode


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
        return ''.join([self.change_font.get(each, each) for each in detail])

    def city_code(self, k):
        return {i.get(k): i for i in self.city_list}

    @staticmethod
    def get_font():
        # 找出字体和字体文件中编码的对应关系,保存为字典
        font_file = TTFont(FONT_FILE)
        font_dict = dict(zip(font_file.getGlyphOrder(), FONT_LIST))
        return {chr(k): font_dict[v] for k, v in font_file['cmap'].getBestCmap().items()}


if __name__ == '__main__':
    pass
