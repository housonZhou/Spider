# coding: utf-8
# Author：houszhou
# Date ：2020/6/1 9:37
# Tool ：PyCharm
import re
from mongoengine import connect, Document, StringField, ObjectIdField

connect('pdsp_beta_db', host='localhost', port=27017)


class GovInfoData(Document):
    extension = ObjectIdField()
    file_type = StringField()
    website = StringField()


def obj_first(obj, error=''):
    return obj[0] if obj else error


def format_file_type(doc_no: str):
    file_first = obj_first(re.findall(r'^(.*?)[〔\[【]', doc_no))
    if file_first:
        file_type = file_first
    elif obj_first(re.findall(r'^(.*?)\d{4}', doc_no)):
        file_type = obj_first(re.findall(r'^(.*?)\d{4}', doc_no))
    elif '第' in doc_no:
        file_type = obj_first(re.findall('^(.*?)第', doc_no))
    elif obj_first(re.findall(r'^(.*?)\d', doc_no)):
        file_type = obj_first(re.findall(r'^(.*?)\d', doc_no))
    else:
        file_type = ''
    return '' if re.findall(r'^\d', file_type) else file_type


def change():
    find_all = GovInfoData.objects(website='北大法宝')  # 返回所有的文档对象列表
    for u in find_all:
        extension = u.extension
        doc_no = extension.get('doc_no', '')
        file_type = format_file_type(doc_no) if doc_no else ''
        print("website:", u.website, "extension:", extension, ",file_type:", u.file_type, 'new file_type: ', file_type)
        u.update(file_type=file_type)


if __name__ == '__main__':
    change()
