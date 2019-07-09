import requests


def base_req(url, **kwargs):
    headers = {
        # 'x-sessionid': '02B929C3-FBDF-47EB-8D1E-05BD8B5547E2',
        'user-agent': 'WeiboOverseas/3.5.2 (iPhone; iOS 12.3.1; Scale/2.00)',
        'accept-language': 'zh-Hans-CN;q=1',
        'accept-encoding': 'br, gzip, deflate'
    }
    return requests.get(url, headers=headers, verify=False)


def demo():
    url = 'https://api.weibo.cn/2/statuses/friends_timeline?advance_enable=false&aid=01AlHVuCZCG69E65drHkFmRd1Lr4lZ94eg6Z6VVuW246VFJ3g.&base_app=0&c=weicoabroad&count=25&from=1235293010&gsid=_2A25wGcj3DeRxGeVJ6lYT8yvFzzmIHXVQj1s_rDV6PUJbkdAKLUX4kWpNT-MPICZR4vQYX2evZw1X3SzLF5XGQn8q&i=3019015&lang=zh_CN&s=aa5460cb&since_id=4390628341480566&ua=iPhone11%2C8_iOS12.3.1_Weibo_intl._3520_wifi&v_p=59'
    data = base_req(url)
    print(data.status_code)
    print(data.content.decode())


if __name__ == '__main__':
    demo()
