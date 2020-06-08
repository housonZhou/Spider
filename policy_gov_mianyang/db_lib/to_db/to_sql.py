#! gmesp_policy_spider-1.0.0/venv python3
# -*- coding: utf-8 -*-
# @Time     : 2020-5-19 15:51
# @Author   : EX-HEYANG002
# @FILE     : to_sql.py
# @IDE     : PyCharm

# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime
import json
import re
import traceback
import uuid
from functools import wraps
from json.decoder import JSONDecodeError

import requests
from scrapy.exceptions import DropItem

from db_lib.to_db.settings import Config
from db_lib.to_db.model import Func, Industry, IndustryLabel, Law, \
    Policy, PolicyDecode, Project, ProjectLabel, PublishAgency
from db_lib.to_db.model import session

c = Config()
MODEL_URL = c.MODEL_URL


def parse_file(fn):
    @wraps(fn)
    def wrapper(instance, item, spider):
        """
        判断是否需要对附件进行解析；根据附件文件类型进行不同的操作
        :param instance: 类实例
        :param item: 数据源
        :param spider: 爬虫对象
        :return:
        """
        matcher = re.search(r'(?:decode|law)', spider)
        if matcher:
            return fn(instance, item, spider)
        files = item.get('files')
        item['files'] = [file.get('path') for file in files] if files else []
        file_title = item.get('attach_title')
        item['attach_title'] = [file for file in file_title] if file_title else []
        attach = []
        # attaches = dict(zip(item['attach_title'], item['files']))
        # for file_title, file_path in attaches.items():
        #     file_path = Path(FILES_STORE).joinpath(file_path).absolute()
        #     try:
        #         if file_path.suffix == '.zip' or file_path.suffix == '.rar':
        #             attach += release_file(file_path)
        #         elif not filter_file(file_title, file_path):
        #             attach.append({'title': file_title, 'content': file2str(file_path)})
        #     except Exception as e:
        #         logging.error(e)
        item['attach'] = attach
        return fn(instance, item, spider)
    return wrapper


class SQLMixin:
    base_url = MODEL_URL
    # push_items_url = 'http://30.23.11.147/api/gmesp/admin/myNews/policy/push'  # 推送爬取政策总条数, 统计爬取的数量暂时未实现

    ORM_REGION = {
        '全国': '000000',
        '国务院': '000000',
        '四川省': '510000',
        '绵阳市': '510700',
        '国家部委': '000000',
        '涪城区': '510703',
        '游仙区': '510704',
        '安州区': '510705',
        '三台县': '510722',
        '盐亭县': '510723'
    }

    @parse_file
    def process(self, item, spider):
        if not item['title']:
            raise DropItem('Spider nothing')
        item['title'] = ''.join(item['title']).strip()
        item['content'] = [re.sub(r'(?:\u3000|\xa0|\s|\u2003)', '', content) for content in item.get('content', [])]
        publish_date = item.get('publish_date')
        if publish_date and isinstance(publish_date, str):
            publish_date = publish_date.split('：')[-1].split(':', maxsplit=1)[-1]
            # publish_date = publish_date.strip().split(' ')[0]
            publish_date = publish_date.strip()
            try:
                try:
                    publish_date = datetime.datetime.strptime(publish_date, '%Y-%m-%d')
                except ValueError:
                    publish_date = datetime.datetime.strptime(publish_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                publish_date = datetime.datetime.strptime(publish_date, '%Y年%m月%d日')
        item['publish_date'] = publish_date

        publish_agency = item.get('publish_agency')
        if publish_agency:
            publish_agency = publish_agency.split('：')[-1].strip()
            if publish_agency.startswith('市'):
                publish_agency = '深圳{}'.format(publish_agency)
            if publish_agency == '来源  :  本网':
                publish_agency = '广东省人民政府办公厅'
            for region, region_id in self.ORM_REGION.items():
                regex = re.compile(region)
                matcher = regex.search(publish_agency)
                if matcher:
                    item['region'] = region_id
        if item.get('region'):
            item['region'] = self.ORM_REGION.get(item['region'], item['region'])
        item['publish_agency'] = publish_agency

        document_id = item.get('file_no')
        item['file_no'] = re.sub(r'(?:\u3000|\xa0)', '', document_id) if document_id else None
        return item

    @staticmethod
    def generate_id(name):
        return uuid.uuid5(uuid.NAMESPACE_DNS, name).hex

    @staticmethod
    def commit(instance):
        if isinstance(instance, list):
            session.add_all(instance)
        else:
            session.add(instance)
        try:
            session.commit()
        except Exception as e:
            session.rollback()

    def policy_decode(self, model, item, spider):
        """
        政策解读数据入库
        :param model:
        :param item: 数据源
        :return:
        """
        item = self.process(item, spider)
        query = self.create_instance(model, item)
        if not isinstance(query, str):
            self.commit(query)
            return query.ID
        return query

    def model_parse(self, item, spider):
        """
        经模型解析
        :param item: 数据源
        :param spider: 爬虫对象
        :return:
        """
        # 请求AI解读模型
        item = self.process(item, spider)
        params = dict(item)
        params['publish_date'] = str(params['publish_date'])
        matcher = re.search(r'law', spider)
        params['source'] = 0 if matcher else 1
        params = json.dumps([params])
        response = requests.post(self.base_url, data=params)
        try:
            resp = response.json()
        except JSONDecodeError:
            resp = response.json(encoding='gbk')
        try:
            # print(resp)
            data = resp['data'][0]
        except IndexError:
            return None

        # 根据返回数据，将数据存入不同的库
        constructed_content = data.get('contructed_content')
        if constructed_content:
            instance = self.create_instance(Policy, item)
            if isinstance(instance, str):
                return None

            constructed = constructed_content[0]    # 将返回的数据装在同一个列表中，后续可能需要去重
            condition = constructed['condition']
            material = constructed['material']
            degree = constructed['degree']
            target = constructed['target']
            if condition:
                instance.APPLICATION = json.dumps(condition, ensure_ascii=False)    # 申请条件
            if material:
                instance.MATERIAL = json.dumps(material, ensure_ascii=False)        # 申请材料
            if degree:
                instance.SUPPORT = json.dumps(degree, ensure_ascii=False)           # 扶持力度
            if target:
                instance.TARGET = json.dumps(target, ensure_ascii=False)            # 扶持对象

            instance.IS_ENTERPRISE = data['is_enterprise']['id']  # 是否涉企

            instance.REGION_ID = item['region']

            valid_period = data.get('valid_period')  # 有效期
            if valid_period:
                valid_period = re.search(r'(\d+)', valid_period)
            if hasattr(instance, 'VALID_PERIOD') and valid_period:
                instance.VALID_PERIOD = int(valid_period.group())

            func_label = data['func_label']   # 功能标签
            if func_label:
                # 查询功能标签表中是否已存在该名称，不存在则新建
                func = session.query(Func).filter(Func.NAME == func_label['name']).first()
                if not func:
                    func = Func()
                    func.NAME = func_label['name']
                    func.ID = self.generate_id(func.NAME)
                    self.commit(func)
                instance.FUNC_LABEL_ID = func.ID

            self.classify('industry_label', data, instance, IndustryLabel, Industry)   # 产业类别
            self.classify('project_label', data, instance, ProjectLabel, Project)      # 项目类别
            self.detail(item, instance)

    def detail(self, item, instance):
        content = item['new_content']   # 正文内容及HTML格式正文内容
        if content:
            instance.CONTENT = json.dumps(content, ensure_ascii=False)
            instance.CONTENT_HTML = json.dumps(item['content_html'], ensure_ascii=False)

        file_urls = item.get('file_urls')   # 附件标题、附件链接、附件路径
        if file_urls:
            instance.ATTACH_TITLE = json.dumps(item['attach_title'], ensure_ascii=False)
            instance.ATTACH_LINK = json.dumps(file_urls, ensure_ascii=False)
            instance.ATTACH_PATH = json.dumps(item['files'], ensure_ascii=False)

        relevant_title = item.get('relevant_title')   # 政策解读ID
        if relevant_title:
            data = {
                'title': relevant_title, 'web_link': item.get('relevant_url'), 'publish_agency': item['publish_agency'],
                'decode': 1, 'publish_date': item['publish_date'], 'website': item['website']
            }
            instance.POLICYDECODE_ID = self.policy_decode(PolicyDecode, data, 'policy_decode')

        self.commit(instance)
        # if isinstance(instance, Policy):
        #     data = {'policyId': instance.ID}  # 反馈政策ID给后台
        #     requests.post(self.push_url, json=data)

    def classify(self, name, data, instance, model, model_name):
        """
        根据数据源，获取类别标签等信息
        :param name: 从数据源获取的标签名
        :param data: 数据源
        :param instance: sqlalchemy orm实例，该项目为Policy或者Law的实例
        :param model: sqlalchemy orm模型，该项目为产业类别表或者项目类别表
        :param model_name: sqlalchemy orm模型， 该项目为产业名称表或者项目名称表
        :return:
        """
        label = data.get(name)
        if label:
            session.query(model).filter(model.POLICY_ID == instance.ID).delete()
            session.commit()
            curds = []
            for item in label:
                # 查询名称表中是否已存在该名称的记录
                label_name = session.query(model_name).filter(model_name.NAME == item['name']).first()
                if not label_name:
                    label_name = model_name()
                    label_name.ID = self.generate_id(item['name'])
                    label_name.NAME = item['name']
                    self.commit(label_name)
                query = model()
                query.RATE = item['rate']
                if model == IndustryLabel:
                    query.INDUSTRY_NAME_ID = label_name.ID
                else:
                    query.PROJECT_NAME_ID = label_name.ID
                query.POLICY_ID = instance.ID
                query.ID = self.generate_id('{}'.format(item['name']).join(instance.ID))
                curds.append(query)
            self.commit(curds)

    def create_instance(self, model, item):
        """
        根据title判断表中是否已存在记录，若存在则判断是否需要更新，不存在则创建模型实例
        :param model: sqlalchemy orm 模型
        :param item: 数据源
        :return:
        """
        query = session.query(model).filter(model.TITLE == item['title']).first()   # 根据title查询表中是否存在
        if query:
            if not query.PUBLISH_DATE or query.PUBLISH_DATE < item['publish_date']:   # 根据发布时间判断是否需要更新
                query = query
            else:
                return query.ID
        else:
            query = model()
            query.CREATE_DATE = datetime.datetime.now()
        query.TITLE = item['title']
        query.ID = self.generate_id(query.TITLE)
        query.WEB_LINK = item['web_link']
        query.WEBSITE = item['website']
        publish_date = item.get('publish_date')
        if publish_date:
            query.PUBLISH_DATE = publish_date
            query.TOP_TIME = query.PUBLISH_DATE
        agency = session.query(PublishAgency).filter(PublishAgency.AGENCY_NAME == item['publish_agency']).first()
        if not agency and item['publish_agency']:
            agency = PublishAgency()
            agency.AGENCY_NAME = item['publish_agency']
            agency.REGION_ID = item['region']
            agency.ID = self.generate_id(agency.AGENCY_NAME)
            self.commit(agency)
        file_no = item.get('file_no')  # 文号
        if file_no:
            query.FILE_NO = file_no
        query.PUBLISH_AGENCY_ID = agency.ID
        return query


class PolicyDecodePipeline(SQLMixin):
    def process_item(self, item, spider='policy_decode'):
        try:
            self.policy_decode(PolicyDecode, item, spider)
        except Exception:
            print(traceback.print_exc())


class LawPipeline(SQLMixin):
    def process_item(self, item, spider='law'):
        self.policy_decode(Law, item, spider)


class PolicyPipeline(SQLMixin):
    def process_item(self, item, spider='policy'):
        self.model_parse(item, spider)

