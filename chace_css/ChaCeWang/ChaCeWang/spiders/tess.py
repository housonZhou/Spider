import json
import os
import re
from collections import defaultdict, Counter

import pytesseract
import requests
from PIL import Image

from chace_css.ChaCeWang.ChaCeWang.settings import HEADERS, COOKIES


class TessOcr:
    def __init__(self):
        self.lock = False
        self.word_list = []
        self.img_dir = r'C:\Users\17337\houszhou\data\SpiderData\查策网\验证码\tess_img'
        self.headers = HEADERS.copy()
        self.headers.update({'Cookie': '; '.join(['{}={}'.format(k, v) for k, v in COOKIES.items()])})

    def do(self):
        if not self.lock:
            self.lock = True
            if self.check():
                print('验证有效期内，无需重复验证!!!')
                self.word_list = []
                self.lock = False
                return
            self.verify()
            # lg = Login()
            # lg.do()
            self.lock = False
        else:
            print('正在验证中，无需重复验证')

    def check(self):
        api_url = 'http://www.chacewang.com/ProjectSearch/FindWithPager?sortField=CreateDateTime&sortOrder=desc&' \
                  'pageindex=0&pageSize=20&cylb=&diqu=RegisterArea_HNDQ_Guangdong_Guangzhou_FY&bumen=&cylbName=&' \
                  'partition=&partitionName=&searchKey=&_=1570608001560'
        response = requests.get(api_url, headers=self.headers)
        req_data = json.loads(response.content.decode())
        return False if req_data.get('Code') == 'WebCrawlerCheckCount' else True

    def verify(self):
        self.update_tess()  # 更新验证码
        self.get_img()  # 获取20张验证码
        self.tess_result()  # 识别验证码000000000000000000000
        for word in self.word_list.copy():
            if self._verify_tess(word):
                print('验证成功!!!', word)
                self.word_list = []
                return
            else:
                print('验证失败:', word)
        print('验证失败，刷新验证码，重新验证')
        self.verify()

    def _verify_tess(self, tess):
        api_url = 'http://www.chacewang.com/Common/CheckVerifyCode?VerifyCode={}&path=%2Fprojectsearch%2Ffindwithpager'.format(
            tess)
        data = requests.get(api_url, headers=self.headers)
        result = json.loads(data.content.decode())
        return result.get('valid', False)

    def update_tess(self):
        api_url = 'http://www.chacewang.com/Common/RefVerifyCode?path=/projectsearch/findwithpager'
        data = requests.get(api_url, headers=self.headers)
        if data.status_code != 200:
            print('更新验证码错误', data)
        else:
            print('更新验证码成功', data)

    def get_img(self):
        print('获取验证码')
        for i in range(20):
            self.req_img(os.path.join(self.img_dir, '{}.jpg'.format(i)))

    def req_img(self, save):
        api_url = 'http://www.chacewang.com/Common/Code?path=/projectsearch/findwithpager'
        data = requests.get(api_url, headers=self.headers)
        with open(save, 'wb')as f:
            f.write(data.content)

    def tess_result(self):
        result_list = []
        for i in os.listdir(self.img_dir):
            img_save = os.path.join(self.img_dir, i)
            result = image2string(img_save)
            result_list += result
        self.word_list = do_tess(result_list)


class Login:
    def __init__(self):
        self.url = 'http://www.chacewang.com/Login/CheckLogin'
        self.lock = False
        self.headers = {
            'Accept': 'text/plain, */*; q=0.01',
            'Origin': 'http://www.chacewang.com',
            'X-Requested-With': 'XMLHttpRequest', 'Referer': 'http://www.chacewang.com/Login/New_Detail',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
            'Cookie': 'czc_mainId=9a90a7ae-66fd-4eb9-b58c-00daf7c95298%2C1c60393a-afdd-409d-b7dd-633d91b56cc8; Hm_lvt_42c061ff773ed320147f84a5220d9dcc=1571295542,1571306430,1571365322,1571714913; Hm_lvt_f9b4d143305c6f75248d93b7b5d8f6f1=1571295542,1571306430,1571365322,1571714913; nb-referrer-hostname=www.chacewang.com; ASP.NET_SessionId=epcq34bsryuep353zubhnca0; currentCity=2a0fc015-7d9a-4446-9cac-416cd61b9efa; Hm_lpvt_42c061ff773ed320147f84a5220d9dcc=1571907524; Hm_lpvt_f9b4d143305c6f75248d93b7b5d8f6f1=1571907524; nb-start-page-url=http%3A%2F%2Fwww.chacewang.com%2FNewHome%2FIndex'}

    def do(self):
        if self.lock:
            print('登录中，请勿重试')
            return
        self.lock = True
        print('登录中')
        result = self.login()
        if result:
            print('登录成功')
        else:
            print('登录失败')
        self.lock = False

    def login(self):
        data = {'Account': '17722431797', 'EnPassword': 'kfuw4z2dnb2w4mbsga4a', 'fakeId': '', 'nmId': ''}
        try:
            req = requests.post(self.url, data=data, headers=self.headers, cookies=COOKIES)
            if req.status_code == 200 and req.content == b'3':
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False


def image2string(img_path):
    """
    从图片中识别出验证码，同时使用两种识别模型
    :param img_path: 图片路径
    :return: [enm识别结果， eng识别结果]
    """
    image = Image.open(img_path)
    image = image.convert('RGB')  # 真彩色
    max_pixel = get_threshold_detail(image)  # 获取背景颜色
    image = image.convert('L')
    table = get_bin_table(max_pixel[0])  # 二值化，黑白
    out = image.point(table, '1')
    # out.save(img_path.replace('.jpg', '_change.jpg'))
    result_enm = pytesseract.image_to_string(out, lang='enm')
    result_eng = pytesseract.image_to_string(out, lang='eng')
    return [result_enm, result_eng]


def get_threshold_detail(image):
    """
    获取图片背景颜色，同时识别验证码图片干扰线，并清除
    """
    pixel_dict = defaultdict(lambda: {'count': 0, 'x': [], 'y': []})
    rows, cols = image.size
    for i in range(rows):
        for j in range(cols):
            pixel = image.getpixel((i, j))
            pixel_dict[pixel]['count'] += 1
            pixel_dict[pixel]['x'].append(i)
            pixel_dict[pixel]['y'].append(j)
    back_color = get_back(pixel_dict)
    line_list = get_line_point(pixel_dict, back_color)
    for each in line_list:
        image.putpixel(each, back_color)  # 清除干扰线
    return back_color


def get_back(pixel_dict):
    count_max = max([i.get('count') for i in pixel_dict.values()])
    pixel_dict_reverse = {v.get('count'): k for k, v in pixel_dict.items()}
    back_color = pixel_dict_reverse[count_max]
    return back_color


def get_line_point(pixel_dict, back_color):
    """
    验证码干扰线的特点：x坐标分布广，几乎不重复
    原理：获取所有颜色的点坐标，除背景颜色外，x坐标大于20个且重复最少的两个颜色，为干扰线颜色，
          返回干扰线不重复的x坐标的点
    缺点：当数字或字母与干扰线的颜色相同时，不能很好地清除干扰线，会在相同颜色的字体处保留干扰线
    """
    new_dict = defaultdict(list)
    need_list = []
    for k, v in pixel_dict.items():
        x_ = v.get('x')
        if len(set(x_)) > 20 and k != back_color:
            y_ = v.get('y')
            point_data = [(x_[i], y_[i]) for i in range(len(x_)) if x_.count(x_[i]) == 1]
            new_dict[len(x_) - len(set(x_))].append({'color': k, 'data': point_data})
    while len(need_list) < 2 and new_dict.keys():
        min_ = min(new_dict.keys())
        need_list += new_dict[min_]
        new_dict.pop(min_)
    line_point_list = []
    for each in need_list:
        line_point_list += each.get('data')
    return line_point_list


def get_bin_table(threshold, rate=0.27):
    return [1 if threshold * (1 - rate) <= i <= threshold * (1 + rate) else 0 for i in range(256)]


def do_tess(result_list):
    """
    清洗模型识别的结果，按照策略输出候选结果：出现次数最多的前3，和每个位置出现最多的前2的组合
    :param result_list: 模型识别的结果列表
    :return: 候选结果列表
    """
    pass_dict = defaultdict(list)
    for each in result_list:
        each = re.sub('\s|\W', '', each)
        if len(each) == 4:
            pass_dict['all'].append(each)
            pass_dict['1'].append(each[0])
            pass_dict['2'].append(each[1])
            pass_dict['3'].append(each[2])
            pass_dict['4'].append(each[3])
    all_list = pass_dict.get('all')
    top_all = top_counter(all_list, index=3)
    tess_list = list(top_all)
    for i in top_counter(pass_dict.get('1')):
        for j in top_counter(pass_dict.get('2')):
            for k in top_counter(pass_dict.get('3')):
                for z in top_counter(pass_dict.get('4')):
                    now_ = ''.join([i, j, k, z])
                    if now_ not in tess_list:
                        tess_list.append(now_)
    return tess_list


def top_counter(need_list, index=2):
    return [i[0] for i in Counter(need_list).most_common(index)]


if __name__ == '__main__':
    # to = TessOcr()
    # for _ in range(20):
    #     th = threading.Thread(target=to.do)
    #     th.start()
    #     time.sleep(4)
    Lg = Login()
    print(Lg.do())
