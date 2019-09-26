from WindPy import w
import pymysql


class MySqlClient:
    def __init__(self):
        self.db = pymysql.connect(host='10.25.76.14', port='3306', user='wind', password='pasc2019', db='qstdata')
        self.cursor = self.db.cursor()

    def __del__(self):
        self.db.close()

    def inset(self):
        sql = "INSERT INTO baidubaike (url, summary)  values(%s, %s);"
        self.cursor.execute(sql, '', '')
        self.db.commit()

    def test_connect(self):
        self.cursor.execute("SELECT version()")
        one_data = self.cursor.fetchone()
        print(one_data)
        return True


class TheWind:
    def __init__(self):
        print('wind start')
        w.start()

    def __del__(self):
        print('wind close')
        w.close()

    @staticmethod
    def df2list(df):
        return df.to_dict(orient='records')

    @staticmethod
    def edb(id_data: dict, begin, end='2019-12-31', save_path=''):
        """
        获取宏观数据库数据
        :param id_data: {指标ID: 指标名称}->{'M5567877': '国内生产总值第一产业', 'M5567885': '国内生产总值住宿和餐饮业'}
        :param begin: 查询开始时间
        :param end:  查询结束时间
        :param save_path:  保存数据为excel，路径为空不保存
        :return: 查询到的数据 类型为pandas.DataFrame
        """
        print('get edb')
        search = ','.join([i for i in id_data])
        error_code, df = w.edb(search, begin, end, 'Fill=Previous', usedf=True)
        if error_code == 0:
            df = df.reset_index()
            id_data.update({'index': 'time'})
            df.rename(columns=id_data, inplace=True)  # 变换原始df列名，索引改为'time'列，其他列按照id_data的字段修改
            if save_path:
                df.to_excel(save_path)
            return df
        else:
            print('api edb error: ', error_code, df)
            return None


def test():
    k = {'M0001380': '国内生产总值第一产业', 'M0001381': '国内生产总值住宿和餐饮业'}
    save = r'C:\Users\17337\houszhou\data\SpiderData\Wind\api.xlsx'
    tw = TheWind()
    data = tw.edb(k, begin='2018-01-01', save_path=save)
    print(data)


if __name__ == '__main__':
    test()
