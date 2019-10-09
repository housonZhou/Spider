import json
import requests
import time
import os

from fontTools.ttLib import TTFont
from lxml.etree import HTML
import pandas as pd


def base_req(url, method='GET', **kwargs):
    base_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}
    headers = kwargs.get('headers', {})
    headers.update(base_headers)
    s = requests.session()
    s.keep_alive = False
    req = s.request(method=method, url=url, headers=headers, verify=False)
    return req


def xpath_string(tree, xpath_name, is_change=True):
    xpath_str = '//div[@class="detail-content project-detail"]/div/p[contains(text(), "{}")]/following-sibling::p'
    con_list = tree.xpath(xpath_str.format(xpath_name))
    result_str = '\n'.join([each.xpath('string(.)') for each in con_list])
    return handle_detail(result_str) if is_change else result_str


def page_detail(tree: HTML):
    name = tree.xpath('//div[@class="detail-title"]/p/text()')[0]
    department = tree.xpath('//*[@id="titleInfo"]/span[@class="detail-type"]/span/text()')[0]
    time_map = tree.xpath('//*[@id="titleInfo"]/span[@class="detail-time"]/text()')  # 无需替换
    category = tree.xpath('//ul[@class="list-unstyleds ccw-font-style"]/li/text()')  # 产业类别
    condition = xpath_string(tree, "申报条件")
    vigor = xpath_string(tree, "支持力度")
    material = xpath_string(tree, "申报材料")
    source = xpath_string(tree, "项目来源", is_change=False)  # 无需替换
    analysis = xpath_string(tree, "项目分析")
    system = xpath_string(tree, "申报系统", is_change=False)  # 无需替换
    result = {'项目名称': handle_detail(name), '受理部门': handle_detail(department),
              '申报时间': ''.join(time_map).strip(), '产业类别': [handle_detail(i) for i in category],
              '申报条件': condition, '支持力度': vigor, '申报材料': material, '项目来源': source, '项目分析': analysis,
              '申报系统': system}
    print(result)
    return result


def get_city():
    pass


def handle_detail(detail):
    font_file = TTFont(r'C:\Users\17337\Downloads\ccw.ttf')
    font_list = [' ', '9', '8', '3', '4', '7', '5', '&', '>', 'c', 'H', 'q', 'S', '#', 'G', 'h', 'E', 'g', 'x',
                 '(', ')', 'R', '/', 'u', 'r', 'd', '=', 'v', 'j', 'Q', 'V', 'i', 'N', 'B', 'T', '$', 'C', 'n',
                 '!', 'p', 's', 'I', '|', 'L', 'F', '%', 'b', '@', 'y', 'Y', '?', '_', 'f', '^', 'Z', 'l', '<',
                 'a', 'o', 'P', 'm', 't', 'W', 'U', 'O', 'A', 'J', 'M', 'e', 'D', 'k', 'z', 'K', 'w', '+', '河',
                 '精', '质', '据', '从', '收', '升', '安', '码', '受', '创', '易', '行', '年', '自', '步', '备',
                 '措', '知', '企', '心', '龙', '因', '集', '限',
                 '及', '列', '配', '专', '贸', '政', '东', '快', '号', '利', '公', '先', '等', '研', '称', '李',
                 '山', '进', '改', '二', '度', '一', '立', '书', '注', '下', '火', '司', '机', '子', '条', '电',
                 '甲', '家', '物', '设', '济', '栋', '助', '励', '天', '策', '小', '五', '光', '当', '有', '乡',
                 '报', '县', '才', '督', '元', '计', '更', '违', '未', '者', '予', '请', '个', '四', '评', '证',
                 '体', '格', '处', '册', '维', '发',
                 '服', '深', '阅', '民', '信', '十', '广', '座', '丙', '云', '中', '任', '首', '华', '单', '道',
                 '保', '万', '事', '新', '项', '与', '询', '术', '提', '件', '股', '扶', '源', '微', '张', '范',
                 '围', '王', '委', '六', '理', '厂', '展', '八', '数', '金', '湖', '属', '罪', '通', '互', '管',
                 '跑', '丁', '获', '资', '型', '网', '授', '值', '街', '算', '包', '准', '经', '名', '给', '并',
                 '基', '地', '工', '复', '原', '息', '批', '园', '点', '过', '西', '来', '额', '免', '间', '符',
                 '需', '务', '持', '部', '能', '活', '已', '国', '程', '得', '镇', '或', '域', '总', '水', '再',
                 '的', '括', '时', '市', '验', '合', '文', '拆', '犯', '产', '错', '百', '学', '重', '辖', '为',
                 '九', '除', '千', '费', '效', '量', '积', '订', '不', '规', '门', '造', '区', '月', '施', '员',
                 '制', '也', '圳', '七', '还', '省', '联', '位', '北', '建', '革', '南', '监', '查', '字', '究',
                 '阳', '须', '全', '导', '会', '大', '份', '日', '厅', '亿', '环', '法', '贴', '币', '类', '科',
                 '申', '技', '城', '别', '海', '标', '目', '乙', '纸', '主', '三', '优', '图', '所', '商', '州',
                 '刘', '种', '变', '奖', '秀', '补', '京', '高', '人', '运', '2', '1', '6', '*', '~', '±', 'X',
                 '业', '院', '⚪', '明', '局', '第']
    print(len(font_list))
    # 找出字体和字体文件中编码的对应关系,保存为字典
    font_dict = dict(zip(font_file.getGlyphOrder(), font_list))
    int_font = {chr(k): font_dict[v] for k, v in font_file['cmap'].getBestCmap().items()}
    new_detail = ''.join([int_font.get(each, each) for each in detail])
    return new_detail


partition = {
    'High-Tech': '总经圳据册第',
    'ESAER': '节水减排',
    'MajorProject': '五员精值',
    'EquityFinancing': '括权配复',
    'ExAnteFunding': '京前配复',
    'SATA': '张圳资改',
    'BySupport': '程套配复',
    'AfterTheFund': '京后配复',
    'LaunchAid': '导获配复',
    'LIDB': '贷款再升再金',
    'Attract': '招主引配',
    'ScaleUp': '扩委上小模',
    'Srtp': '张导订精',
    'InnovativePlatform': '标经载环',
    'HQHeadquarte': '贴数册第',
    'EventsPlanner': '司动革划',
    'LittleMicro': '间格李册第',
    'LargeEnterprises': '员批册第',
    'Agency': '间介机属',
    'NGO': '社园组织',
    'ManufachuringMoney': '委第山码',
    'AppliedModel': '应用示立',
    'Standardization': '知全化',
    'TechnicalReform': '圳据地心',
    'CCIA': '委第阳盟',
    'RisingEconomy': '经兴委第',
    'Industries': '传统委第',
    'CITL': '除别份流',
    'RADOP': '导获间试',
    'Manufacturing': '委第化',
    'TIAF': '罪光认定究配复',
    'BAMD': '品牌究网场开拓',
    'IPR': '才识委权',
    'InformationAndIntegration': '集升化>两化融为',
}
city = {
    '上海': 'RegisterArea_ZXS_Shanghai',
    '北京': 'RegisterArea_ZXS_Beijing',
    '广州': 'RegisterArea_HNDQ_Guangdong_Guangzhou',
    '杭州': 'RegisterArea_HDDQ_Zhejiang_HangZhou',
}


def test():
    test_list = [
        'f8120468-dac4-4401-81d3-788c56fe5272',
        '9f573200-342f-45a0-9efd-03a2f10e7a66',
        'adb2be5d-0f06-4e39-804d-4ea2a7049ecb',
        'ada2da24-1ba9-463e-978f-56d64968a5af',
        '4d961b79-3364-447f-ac48-a2728f172e1b',
        '64ee35fa-01c4-441d-ab70-fab28a1feaed',
        'd8400349-1d8e-4446-91a6-1838be67b8b3',
        '5c5ba0ca-1d06-47bf-bf47-ba173974b5ac',
        'ac490d4c-4f27-445c-bccb-de6a122c636e',
        'e793a184-7674-4bed-96d3-21637055e117',
        '280faac3-5ad3-4ac7-87f4-c65342cbd023'
    ]
    info = {'城市': '深圳', '地区': '南山', '项目类别': '高新技术企业'}
    data_result = []
    for main_id in test_list:
        url = 'http://www.chacewang.com/ProjectSearch/NewPeDetail/{}?from=home'.format(main_id)
        response = base_req(url)
        data = page_detail(HTML(response.text))
        info_ = info.copy()
        info_.update(data)
        data_result.append(info_)
        time.sleep(3)
    pd.DataFrame(data_result).to_excel(r'C:\Users\17337\houszhou\data\SpiderData\查策网\demo.xlsx')


def deal():
    dir_path = r'C:\Users\17337\houszhou\data\SpiderData\查策网\done'
    df_list = [pd.read_excel(os.path.join(dir_path, item)) for item in os.listdir(dir_path)]
    new_df = pd.concat(df_list, sort=False)
    # save_list = []
    # for each in new_df.to_dict(orient='records'):
    #     type_str = each.get('产业类别', '[]')
    #     type_str = type_str.replace('\'', '"')
    #     type_list = json.loads(type_str)
    #     for type_name in type_list:
    #         this_data = each.copy()
    #         this_data.update({'产业类别': type_name, '所有产业类别': type_str})
    #         save_list.append(this_data)
    # save_df = pd.DataFrame(save_list)
    new_df.to_excel(r'C:\Users\17337\houszhou\data\SpiderData\查策网\查策网6区域数据0930_不重复.xlsx')


if __name__ == '__main__':
    # url = 'http://www.chacewang.com/ProjectSearch/NewPeDetail/6f5bb3c7-f329-4f7b-92ae-558ff4ebfae0?from=home'
    # data = base_req(url)
    # print(data.content)
    # de = '1029并2信2源-1025并21信62源期受栋火在海事张圳镇图括权投配（目列）二构、山码（目列二构）、集托、名阳评码融、财富目列二构当码融册第。（括权投配（目列）册第书间算华券投配山码第协园步案华局；其他册第书科供相关牌照）'
    # new_ = handle_detail(de)
    # print(new_)
    # test()
    deal()
