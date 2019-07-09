import mitmproxy
from mitmproxy import http, ctx


class Counter:
    def __init__(self):
        self.num = 0

    def request(self, flow:mitmproxy.http.HTTPFlow):
        self.num += 1
        ctx.log.info("we've seen {} flows".format(self.num))
