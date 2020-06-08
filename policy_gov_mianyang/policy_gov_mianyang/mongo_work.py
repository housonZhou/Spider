# coding: utf-8
# Author：houszhou
# Date ：2020/6/2 14:03
# Tool ：PyCharm
import pymongo
import re


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
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client.pdsp_beta_db
    collection = db.gov_info_data
    result = collection.find({'website': '北大法宝'})
    for i, data in enumerate(result):
        if i % 1000 == 0:
            print(i)
        id_ = data.get('_id')
        extension = data.get('extension')
        doc_no = extension.get('doc_no', '')
        file_type = format_file_type(doc_no) if doc_no else ''
        print('id: {}, doc_no: {}, new_file_type: {}'.format(id_, doc_no, file_type))
        collection.find_one_and_update({'_id': id_}, {'$set': {'file_type': file_type}})


if __name__ == '__main__':
    change()
