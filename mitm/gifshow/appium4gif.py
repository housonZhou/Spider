import time
from appium import webdriver


class GifShow(object):
    def __init__(self):
        desired_caps = {
            'platformName': 'Android',
            'platformVersion': '5.1',
            'deviceName': 'Android Emulator',
            'appPackage': 'com.smile.gifmaker',
            'appActivity': 'com.yxcorp.gifshow.HomeActivity',
        }
        self.driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', desired_caps)
        self.driver.implicitly_wait(3)

    def run(self, swipe_num):
        """
        循环往下滑动app界面
        :param swipe_num: 滑动次数，为负数时死循环滑动
        """
        print('run')
        while True:
            if swipe_num == 0:
                break
            print('touch move')
            self.driver.swipe(342, 1172, 346, 275, 200)
            time.sleep(1.5)
            if swipe_num:
                swipe_num -= 1


if __name__ == '__main__':
    gs = GifShow()
    gs.run(swipe_num=-1)
