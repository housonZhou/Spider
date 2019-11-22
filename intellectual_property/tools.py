import time

import pymongo
import requests
from pymongo.collection import Collection
from pymongo.database import Database
from requests.packages.urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def retry(count=5, default_return=None, sleep_time=0):
    def _first(func):
        def _next(*args, **kwargs):
            nonlocal count
            count -= 1
            try:
                result = func(*args, **kwargs)
                if result.status_code != 200:
                    print(result.url, result.status_code, result.content.decode(), sep='\n')
                    time.sleep(sleep_time)
                    result = _next(*args, **kwargs) if count > 0 else default_return
            except Exception as e:
                print('func: {}, error: {}'.format(func.__name__, e))
                time.sleep(sleep_time)
                result = _next(*args, **kwargs) if count > 0 else default_return
            return result

        return _next

    return _first


@retry(sleep_time=1)
def base_req(method, url, **kwargs):
    s = requests.session()
    s.keep_alive = False
    return s.request(method=method, url=url, verify=False, **kwargs)


def get_first(item=None, else_data=''):
    return item[0] if item else else_data


class MongoDbClient:
    """
    mg = MongoDbClient()
    mg.client_db('db')
    mg.client_col('test')
    data = [{'a': 1, 'b': 1}, {'a': 2, 'b': 2}, {'a': 3, 'b': 3}]
    print(mg.insert_if_not_exist(data, key='a'))
    """

    def __init__(self, host='localhost', port=27017):
        self.client = pymongo.MongoClient(host=host, port=port)
        self._db: Database = None
        self._col: Collection = None

    def __del__(self):
        self.client.close()

    def client_db(self, db):
        self._db = self.client[db]
        print('client db: ', self._db)

    def client_col(self, col_name):
        self._col = self._db[col_name]
        print('client collection:', self._col)

    def insert_many(self, documents=None):
        return self._col.insert_many(documents) if documents else None

    def find_one(self, one):
        return self._col.find_one(one) if one else None

    def insert_if_not_exist(self, documents, key: str):
        """
        逐条查询documents中key的值是否存在，若不存在则插入该条数据
        """
        need_update = [doc for doc in documents if not self.find_one({key: doc.get(key)})]
        result = self.insert_many(need_update)
        print('result: documents: {}, not exists: {}, insert: {}'.format(
            len(documents), len(need_update), len(result.inserted_ids) if result else 0))
        return result


if __name__ == '__main__':
    pass
