# coding: utf-8
# Author：houszhou
# Date ：2020/5/27 17:52
# Tool ：PyCharm
ENV = 'debug'
# ENV = 'format'

FILE_EXCEL = r'C:\Users\17337\houszhou\code\PingAn\Spider\policy_gov_mianyang\db_lib\files'


class DeBug:
    """ 测试环境配置 """
    # 业务数据库
    DB_USERNAME = 'root'
    DB_PASSWORD = 'Root@123ASD'
    DB_HOST = '10.12.81.19'
    DB_PORT = 3306
    DATABASE = 'my-es'

    MODEL_EXCEL = r'C:\Users\17337\houszhou\data\SpiderData\发改营商环境\test\model'  # 模型数据保存excel
    SPIDER_EXCEL = r'C:\Users\17337\houszhou\data\SpiderData\发改营商环境\test\spider'  # 爬虫数据保存excel
    MODEL_URL = 'http://10.12.81.32:8075/extract'  # 接口模型链接


class Format:
    """ 正式环境配置 """
    # 业务数据库
    DB_USERNAME = 'root'
    DB_PASSWORD = 'Root@123ASD'
    DB_HOST = '10.6.29.47'
    DB_PORT = 3306
    DATABASE = 'my-es'

    MODEL_EXCEL = 'format'  # 模型数据保存excel
    SPIDER_EXCEL = 'format'  # 爬虫数据保存excel
    MODEL_URL = 'http://10.6.29.160:8075/extract'  # 接口模型链接


class Config:
    env = {'debug': DeBug(), 'format': Format()}

    def __init__(self, env=ENV):
        self._model = self.env.get(env.lower(), DeBug())

    def __getattr__(self, item):
        return self._model.__getattribute__(item)


if __name__ == '__main__':
    c = Config()
    print(c.DB_USERNAME)
