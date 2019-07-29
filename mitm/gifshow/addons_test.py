import json
import mitmproxy.http
from mitmproxy import ctx, command
import typing

from mitmproxy import ctx
from mitmproxy import exceptions


class Download:

    def not_exisit(self, flow):
        return

    def response(self, flow: mitmproxy.http.HTTPFlow):
        ctx.log.info('========response log 1')
        if flow.request.url:
            flow.response = mitmproxy.http.HTTPResponse.make()
        # flow.request.url = 'http://www.baidu.com'
        # yield ''
        return
        # flow.request.url = 'http://www.baidu.com'

    def request(self, flow: mitmproxy.http.HTTPFlow):
        pass
        # if flow.request.host == '103.107.217.2':
        #     flow.request.url = 'http://www.baidu.com'
        #     ctx.log.info('==================url change')
        ctx.log.info('request log 1')
        ctx.log.info(flow.response.__repr__())


class Upload:
    def response(self, flow: mitmproxy.http.HTTPFlow):
        # ctx.log.info(flow.request.url)
        ctx.log.info('response log 2')
        yield
        # ctx.log.info(flow.response.text)

    def request(self, flow: mitmproxy.http.HTTPFlow):
        if flow.request.url == 'http://www.baidu.com':
            ctx.log.info('response log 2 -> baidu')
        else:
            ctx.log.info(flow.request.url)
        # ctx.log.info('requests log 2')


class Upload3:
    def load(self, loader):
        loader.add_option(
            name="addheader",
            typespec=typing.Optional[int],
            default=1,
            help="Add a header to responses",
        )

    def configure(self, updates):
        if "addheader" in updates:
            if ctx.options.addheader is not None and ctx.options.addheader > 100:
                raise exceptions.OptionsError("addheader must be <= 100")

    def response(self, flow):

        ctx.log.info('==' * 20)
        if ctx.options.addheader is not None:
            ctx.log.info('**' * 20)
            flow.response.headers["addheader"] = str(ctx.options.addheader)
            ctx.log.info(json.dumps(dict(flow.response.headers)))


addons = [Upload3()]  # 按顺序执行
