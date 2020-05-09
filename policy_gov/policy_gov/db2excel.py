import os

import pymysql
import pandas as pd
from collections import defaultdict

from policy_gov.settings import DB_INFO


class PolicyReformPipeline(object):
    def __init__(self):
        self.con = pymysql.connect(**DB_INFO)
        self.cur = self.con.cursor()

    def execute(self, sql, meta=None, result=False):
        self.cur.execute(sql, meta)
        if result:
            return self.cur.fetchall()

    def __del__(self):
        self.con.close()


def main(date):
    pp = PolicyReformPipeline()
    select_sql = """
    SELECT 
    `zhengce_gov`.`id`,
    `zhengce_gov`.`row_id`,
    `zhengce_gov`.`content`,
    `zhengce_gov`.`website`,
    `zhengce_gov`.`source_module`,
    `zhengce_gov`.`url`,
    `zhengce_gov`.`title`,
    `zhengce_gov`.`classify`,
    `zhengce_gov`.`source`,
    `zhengce_gov`.`file_type`,
    `zhengce_gov`.`category`,
    `zhengce_gov`.`publish_time`,
    `zhengce_gov`.`html_content`,
    `zhengce_gov`.`extension`,
    `zhengce_gov`.`create_time`,
    `zhengce_gov`.`update_time`
    FROM `policy_reform`.`zhengce_gov` 
    WHERE create_time > '{}';
    """.format(date)
    result = pp.execute(select_sql, result=True)
    write_json = defaultdict(list)
    for item in result:
        _, row_id, content, website, source_module, url, title, classify, source, file_type, category, publish_time, html_content, extension, *_ = item
        data = {
            'row_id#信息公告id#String': row_id,
            'content#数据原文#String': content,
            'website#数据来源网站名#String': website,
            'source_module#数据来源网址板块#String': source_module,
            'url#网页url#String': url,
            'title#名称(标题)#String': title,
            'classify#所属分类#String': classify,
            'source#信息来源#String': source,
            'file_type#效力级别#String': file_type,
            'category#所属类别#String': category,
            'publish_time#发布时间#String': publish_time,
            'html_content#html原文#String': html_content,
            'extension#扩展字段#json': extension,
        }
        write_json[website].append(data)
    save_dir = r'C:\Users\17337\houszhou\data\SpiderData\发改人民政府政策\excel'
    for website, write_list in write_json.items():
        save_path = os.path.join(save_dir, '{}_{}.xlsx'.format(website, ''.join(date.split('-'))))
        df = pd.DataFrame(write_list)
        df.to_excel(save_path, index=False)


def split_title(excel_file, save_file):
    df = pd.read_excel(excel_file)
    title_list = df.columns.values
    # print(title_list)
    df.rename(columns={name: name.split('#')[0] for name in title_list}, inplace=True)
    df.to_excel(save_file, index=False)


if __name__ == '__main__':
    main('2020-05-07')
    # split_title(r"C:\Users\17337\houszhou\data\SpiderData\发改政策\new\上海市人民政府_20200423.xlsx",
    #             r"C:\Users\17337\houszhou\data\SpiderData\发改政策\new\上海市人民政府_20200423_split.xlsx")
