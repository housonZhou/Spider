import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def retry(count=5, default_return=None, sleep_time=0):
    def _first(func):
        def _next(*args, **kwargs):
            nonlocal count
            count -= 1
            try:
                result = func(*args, **kwargs)
                if result.status_code != 200:
                    print(result.url, result.status_code, result.content.decode(), sep='\n')
                    time.sleep(sleep_time)
                    result = _next(*args, **kwargs) if count > 0 else default_return
            except Exception as e:
                print('func: {}, error: {}'.format(func.__name__, e))
                time.sleep(sleep_time)
                result = _next(*args, **kwargs) if count > 0 else default_return
            return result

        return _next

    return _first


@retry(sleep_time=1)
def base_req(method, url, **kwargs):
    s = requests.session()
    s.keep_alive = False
    return s.request(method=method, url=url, verify=False, **kwargs)


def get_first(item=None, else_data=''):
    return item[0] if item else else_data
