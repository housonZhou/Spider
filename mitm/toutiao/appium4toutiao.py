import time
from appium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TouTiao:
    def __init__(self):
        desired_caps = {
            'platformName': 'Android',
            'platformVersion': '5.1',
            'deviceName': 'Android Emulator',
            'appPackage': 'com.ss.android.article.news',
            'appActivity': '.activity.MainActivity',
        }
        self.driver = webdriver.Remote('http://127.0.0.1:4723/wd/hub', desired_caps)
        self.wait = WebDriverWait(self.driver, 40)
        self.wait.until(EC.presence_of_element_located((By.XPATH, '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout[1]/android.widget.TabHost/android.widget.FrameLayout[2]/android.support.v4.view.ViewPager/android.widget.FrameLayout/android.widget.LinearLayout/android.support.v7.widget.RecyclerView/android.widget.LinearLayout[1]/android.widget.FrameLayout')))

    def run(self, swipe_num):
        """
        循环往下滑动app界面
        :param swipe_num: 滑动次数，为负数时死循环滑动
        """
        print('run')
        while True:
            start = time.time()
            if swipe_num == 0:
                break
            print('touch move')
            self.driver.swipe(342, 1100, 346, 300, 200)
            # time.sleep(1.5)
            if swipe_num:
                swipe_num -= 1
            print('耗时：', time.time() - start)


if __name__ == '__main__':
    tt = TouTiao()
    tt.run(-1)
