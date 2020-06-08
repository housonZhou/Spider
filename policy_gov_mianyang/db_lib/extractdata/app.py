# uncompyle6 version 3.6.6
# Python bytecode 3.7 (3394)
# Decompiled from: Python 3.6.8 (tags/v3.6.8:3c6b436a57, Dec 24 2018, 00:16:47) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: D://外发//svn//Policy//extractdata\extractdata\extractdata\app.py
# Compiled at: 2020-04-20 15:05:11
# Size of source mod 2**32: 4131 bytes
import re

import gensim
import numpy as np
import pandas as pd

from db_lib.extractdata.constant import INDUSTRY_KEYWORDS, INDUSTRY_NUM
from db_lib.extractdata.similarity import FuncClass

word_path = r'C:\Users\17337\Desktop\算法\extractdata_uncompyle\extractdata\extractdata\word_embedded\word_vec_100.bin'
WORD_VEC = gensim.models.KeyedVectors.load_word2vec_format(word_path, binary=True,
                                                           unicode_errors='ignore')


class Industry:

    def __init__(self, wv_model):
        """
        类的初始化构造方法
        :param wv_model: 词向量模型
        :param embedding_size: 词向量大小
        """
        self.model = wv_model

    def match_label(self, types_list, keywords_list, content, coefficient):
        """
        :param types_list:  类别列表
        :param keywords_list: 关键词列表
        :param content: 匹配内容
        :param coefficient: 权重系数
        :return: 类别，匹配度
        """
        sim = FuncClass()
        labels = []
        match_rates = []
        for i in range(len(types_list)):
            rates = []
            count = 0
            for key_word in keywords_list[i]:
                test = re.compile(key_word)
                count = count + len(re.findall(test, content))
                if len(re.findall(test, content)) > 0:
                    try:
                        keyword_vec = sim.word_list_vec([key_word], WORD_VEC, 100)
                        indus_vec = sim.word_list_vec([keywords_list[i][0]], WORD_VEC, 100)
                        rate = coefficient * sim.word_cosine_similarity(keyword_vec[0], indus_vec[0])
                    except:
                        rate = 0.65

                    rates.append(rate)

            if count > 0:
                labels.append(types_list[i])
                match_rate = np.average(rates)
                match_rates.append(match_rate)

        return (
            labels, match_rates)

    def match_labels(self, keywords_dict, content, df_label, coefficient):
        """
        根据关键词去匹配行业类别，进行行业分类
        :param keywords_dict: 类别关键词字典
        :param content: 政策匹配内容
        :param df_label: 政策与各类别初始匹配度
        :param coefficient: 政策匹配内容权重系数
        :return: 政策与各类别匹配度
        """
        pd.set_option('precision', 4)
        types_list = list(keywords_dict.keys())
        keywords_list = list(keywords_dict.values())
        labels, match_rates = self.match_label(types_list, keywords_list, content, coefficient)
        for z in range(len(labels)):
            if df_label.iloc[0][labels[z]] < match_rates[z]:
                df_label.iloc[0][labels[z]] = match_rates[z] * 100

        return df_label

    def df_initialize(self, keywords_dict):
        """
        :param keywords_dict: 类别关键词字典
        :return: 列为各类别名称，值为0的数据框
        """
        types_list = list(keywords_dict.keys())
        dataframe = pd.DataFrame(index=[1], columns=types_list, dtype='double')
        dataframe.loc[:, :] = 0.0
        return dataframe

    def predict(self, title, content):
        """
        预测行业类别，并返回相应的匹配度
        :param title: 文件标题
        :param content: 文件内容
        :return: 政策产业类别及其匹配度
        """
        industry_label_df = self.df_initialize(INDUSTRY_KEYWORDS)
        industry_t = self.match_labels(INDUSTRY_KEYWORDS, title, industry_label_df, 1)
        industry_c = self.match_labels(INDUSTRY_KEYWORDS, content, industry_t, 0.6)
        result = []
        for type_ in industry_c.columns.tolist():
            if industry_c.iloc[0][type_] > 0:
                dict = {'id': INDUSTRY_NUM[type_],
                        'name': type_, 'rate': industry_c.iloc[0][type_]}
                result.append(dict)

        return result


Ind = Industry(WORD_VEC)


def get_ind(title, content):
    res = Ind.predict(title, content)
    ind_id = [item['id'] for item in res]
    return ind_id
