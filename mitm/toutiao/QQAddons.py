import json
from mitmproxy import ctx, http


class QQ:
    def response(self, flow: http.HTTPFlow):
        if ('qq.com' or 'getQQNewsUnreadList') not in flow.request.url:
            return
        url = flow.request.url
        ctx.log.info(url)
        text = flow.response.text
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


save_path = r'TouTiao_news.json'
addons = [TouTiao()]
