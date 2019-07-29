import json
import mitmproxy.http
from mitmproxy import ctx


class Download:
    def response(self, flow: mitmproxy.http.HTTPFlow):
        if flow.request.host != 'api.gifshow.com' or flow.request.method != 'POST':
            return
        url = flow.request.url
        data = flow.response.content.decode()
        if 'hot' in url and 'feeds' in json.loads(data):
            ctx.log.info('get a url:{}'.format(url))
            with open('GifShow.json', 'a', encoding='utf8')as f:
                f.write(json.dumps(data) + '\n')


addons = [Download()]
