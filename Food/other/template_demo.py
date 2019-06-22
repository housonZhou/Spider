

def give_detail_reason_templates(month_pred, types, *args, **kwargs):
    if types == '最高气温':
        template = '{}, 预计本月将有{}天天气最高温度高于{}摄氏度，{}不合格率可能较高，风险等级：{}，建议此期间内对{}组织抽检'
    elif types == '最低气温':
        template = '{}, 预计本月将有{}天天气最低温度低于{}摄氏度，{}不合格率可能较高，风险等级：{}，建议此期间内对{}组织抽检'
    elif types == '温差大':
        template = '{}, 预计本月将有{}天昼夜天气温差大于{}摄氏度，{}不合格率可能较高，风险等级：{}，建议此期间内对{}组织抽检'
    elif types == '温差小':
        template = '{}, 预计本月将有{}天昼夜天气温差小于{}摄氏度，{}不合格率可能较高，风险等级：{}，建议此期间内对{}组织抽检'
    elif types == '舆情':
        template = '{}，近期发生关于{}的负面舆情，{}不合格率可能较高，风险等级：{}，建议此期间内对{}组织抽检'
    else:
        template = ''
        pass

    return template
