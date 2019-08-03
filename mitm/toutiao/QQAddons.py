import json
from mitmproxy import ctx, http


class QQ:
    def request(self, flow: http.HTTPFlow):
        if '.apk' in flow.request.url and flow.request.method == 'GET':
            flow.request.url = ''

    def response(self, flow: http.HTTPFlow):
        if 'getQQNewsUnreadList' not in flow.request.url or flow.request.method != 'POST':
            return
        url = flow.request.url
        ctx.log.info(url)
        text = flow.response.content.decode()
        data = {'url': url, 'text': text}
        with open(save_path, 'a', encoding='utf8')as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')


class TouTiao:
    def response(self, flow: http.HTTPFlow):
        if 'snssdk.com/api/news' not in flow.request.url:
            return
        url = flow.request.url
        ctx.log.info(url)
        text = flow.response.text
        data = {'url': url, 'text': text}
        with open(save_path, 'a', encoding='utf8')as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')


save_path = r'C:\Users\17337\houszhou\data\SpiderData\QQNews\news0730.json'
addons = [QQ()]
