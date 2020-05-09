# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PolicyReformItem(scrapy.Item):
    row_id = scrapy.Field()
    content = scrapy.Field()  # 原文（保留格式）
    website = scrapy.Field()  # 数据来源网站名， eg:浙江省人民政府
    source_module = scrapy.Field()  # 数据来源网址板块， eg:浙江省-人民政府-疫情通告
    url = scrapy.Field()
    title = scrapy.Field()
    file_type = scrapy.Field()  # 效力级别：文号的左边部分  eg: 深府规
    source = scrapy.Field()  # 信息来源，无则用website
    classify = scrapy.Field()  # 所属分类，对应模块标签， eg: 政府文件
    category = scrapy.Field()  # 所属类别，名称-地区-采集模块， eg:人民政府-国家-中央政府文件
    publish_time = scrapy.Field()  # 发布时间
    html_content = scrapy.Field()  # html原文
    extension = scrapy.Field()  # 扩展字段


extension_default = {
    'doc_no': '',  # 文号, eg:深府规【2018】12号
    'index_no': '',  # 索引号， eg：00000-10-2018-000
    'theme': '',  # 主题词
    'write_time': '',  # 成文日期
    'is_effective': '',  # 现行有效，失效，尚未生效
    'effective_start': '',  # 生效开始时间
    'file_name': [],
    'file_type': [],  # 附件所属类别， eg:相关政策解读，无则空
    'file_url': [],
}
