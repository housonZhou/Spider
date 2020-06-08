# uncompyle6 version 3.6.6
# Python bytecode 3.7 (3394)
# Decompiled from: Python 3.6.8 (tags/v3.6.8:3c6b436a57, Dec 24 2018, 00:16:47) [MSC v.1916 64 bit (AMD64)]
# Embedded file name: D://外发//svn//Policy//extractdata\extractdata\extractdata\similarity.py
# Compiled at: 2020-04-16 20:48:09
# Size of source mod 2**32: 6822 bytes
from collections import Counter

import jieba.analyse
import jieba.posseg as pseg
import numpy as np


class FuncClass(object):

    def _word_vec(self, word, wv_model, embedding_size):
        """
        获得单个单词的词向量, 若该词在词向量中不存在，就返回空
        :param word: 单个单词
        :param wv_model: 词向量模型
        :return: 词向量，布尔值（判断词是否在词向量中）
        """
        try:
            vec = wv_model.wv[word]
            return vec
        except:
            return

    def word_list_vec(self, words, wv_model, embedding_size, seg=True):
        """
        获得多个词的向量表示，对获得的词向量以矩阵的形式返回
        :param words: 要获取向量的词的列表
        :param wv_model: 词向量模型
        :param embedding_size: 词向量大小
        :param seg: 是否对不在词向量中的词做进一步分词，然后取平均值
        :param title_len: 主要是用在计算标题的向量时，对标题过长，我们对其取n-gram的形式将标题返回多个值，
                        然后只要其中最大的值大于临界值即可。
        :return:
        """

        def mean(vec):
            vec_np = np.array(vec)
            vec_mean = np.mean(vec_np, axis=0)
            return vec_mean

        words_ = []
        vectors = []
        for word in words:
            vec = self._word_vec(word, wv_model, embedding_size)
            if vec is not None:
                vectors.append(vec)
                words_.append(word)
            elif seg:
                sub_words = jieba.lcut(word)
                sub_vecs = []
                for sub_word in sub_words:
                    sub_vec = self._word_vec(sub_word, wv_model, embedding_size)
                    if sub_vec is not None:
                        sub_vecs.append(sub_vec)

            if sub_vecs:
                vec_ = mean(sub_vecs)
                vectors.append(vec_)
                words_.append(word)

        vectors_np = np.array(vectors)
        return (
            vectors_np, words_)

    def extract_key_words(self, content, top_k, mode='jieba'):
        """
        利用textrank4zh开源工具抽取关键词
        :param content: 输入文本内容
        :param top_k: 关键词个数
        :return: 关键词和权重
        """
        key_words = jieba.analyse.textrank(content, top_k, withWeight=True, allowPOS=['n'])
        words = [item[0] for item in key_words]
        weights = [item[1] for item in key_words]
        return (
            words, weights)

    def cosine_similarity(self, matrix_a, matrix_b):
        """
        计算两个矩阵中向量的相似度
        :param matrix_a: 矩阵a 维度m*d
        :param matrix_b: 矩阵b 维度n*d
        :return: 维度为m*n的矩阵，里面每个值都是关键词和标签的余弦相似度
        """
        matrix_b_t = matrix_b.T
        a_sqrt_sum = np.power(np.sum((np.power(matrix_a, 2)), axis=1), 0.5)
        b_sqrt_sum = np.power(np.sum((np.power(matrix_b_t, 2)), axis=0), 0.5)
        a_shape = a_sqrt_sum.shape[0]
        b_shape = b_sqrt_sum.shape[0]
        a_reshape = np.reshape(a_sqrt_sum, [a_shape, 1])
        b_reshape = np.reshape(b_sqrt_sum, [1, b_shape])
        divisor = np.dot(a_reshape, b_reshape)
        sim_matrix = np.divide(np.dot(matrix_a, matrix_b_t), divisor)
        return sim_matrix

    def word_cosine_similarity(self, matrix_a, matrix_b):
        """
        计算两个矩阵中向量的相似度
        :param matrix_a: 矩阵a 维度m*d
        :param matrix_b: 矩阵b 维度n*d
        :return: 维度为m*n的矩阵，里面每个值都是关键词和标签的余弦相似度
        """
        matrix_b_t = matrix_b.T
        a_sqrt_sum = np.power(np.sum((np.power(matrix_a, 2)), axis=1), 0.5)
        b_sqrt_sum = np.power(np.sum((np.power(matrix_b_t, 2)), axis=0), 0.5)
        a_shape = a_sqrt_sum.shape[0]
        b_shape = b_sqrt_sum.shape[0]
        a_reshape = np.reshape(a_sqrt_sum, [a_shape, 1])
        b_reshape = np.reshape(b_sqrt_sum, [1, b_shape])
        divisor = np.dot(a_reshape, b_reshape)
        sim_matrix = np.divide(np.dot(matrix_a, matrix_b_t), divisor)
        sim = (sim_matrix + 1) / 2
        return sim

    def n_gram(self, tokens, n):
        """
        返回n_gram分词结果
        :param tokens: 单条句子的分词结果，为list
        :param n: 支持int类型和list类型
        :return:
        """
        if isinstance(n, int):
            return [''.join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
        if isinstance(n, list):
            n_gram_list = []
            for item in n:
                n_gram_list.extend([''.join(tokens[i:i + item]) for i in range(len(tokens) - item + 1)])

            return n_gram_list

    def word_freq(self, subject):
        """
        统计文章的词频
        :param subject:
        :return:
        """
        words = []
        for token in subject:
            words.extend(token)

        word_count = Counter(words)
        sort_word_count = sorted((word_count.items()), key=(lambda x: x[1]), reverse=True)
        word = [item[0] for item in sort_word_count if item[1] > 2]
        return (
            word, len(word))

    def extract_noun_words(self, text):
        """
        词性标注获得名词
        :param text:
        :return:
        """
        lines = [pseg.cut(line) for line in text]
        noun_words = []
        for words in lines:
            for word, pos in words:
                if pos == 'n':
                    noun_words.append(word)

        return list(set(noun_words))
