from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
import time
from PIL import Image
from io import BytesIO

THRESHOLD = 60
LEFT = 60
BORDER = 6
USERNAME: str = '1733776802@qq.com'  # b站账号、邮箱
PASSWORD: str = ''  # 密码


class CrackGeeTest:
    def __init__(self):
        self.url = "https://passport.bilibili.com/login"
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.username = USERNAME
        self.password = PASSWORD

    def __del__(self):
        self.browser.close()

    def open(self) -> None:
        """
        打开登录页面，输入帐号和密码
        :return:
        """
        self.browser.get(self.url)
        email = self.wait.until(EC.presence_of_element_located((By.ID, 'login-username')))
        email.send_keys(self.username)
        time.sleep(0.5)
        password = self.wait.until(EC.presence_of_element_located((By.ID, 'login-passwd')))
        password.send_keys(self.password)
        time.sleep(0.5)

    def get_geetest_button(self):
        return self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-login")))

    def get_geetest_image(self, name, full):
        """
        输入文件名，保存验证码图片
        :param name: 保存的文件名
        :param full: True->无缺口组件图片；False->有缺口组件图片
        :return: 截取的验证码图片
        """
        top, bottom, left, right, size = self.get_position(full)
        screenshot = self.get_screenshot()
        screenshot.save('bilibili.png')
        captcha = screenshot.crop(
            (left * 1.5, top * 1.5, right * 1.5, bottom * 1.5))
        size = size["width"] - 1, size["height"] - 1
        captcha.thumbnail(size)
        captcha.save(name)
        return captcha

    def get_position(self, full):
        """
        获取验证码图片位置信息
        :param full: 为True时浏览器会加载完整验证码图片
        :return: 验证码图片位置
        """
        img = self.wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "geetest_canvas_img")))
        fullbg = self.wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "geetest_canvas_fullbg")))
        time.sleep(2)
        # 改变样式，获得不同图片
        if full:
            self.browser.execute_script(
                "arguments[0].setAttribute(arguments[1], arguments[2])", fullbg, "style", "")
        else:
            self.browser.execute_script(
                "arguments[0].setAttribute(arguments[1], arguments[2])", fullbg, "style", "display: none")

        location = img.location
        size = img.size
        top, bottom, left, right = location["y"], location["y"] + size["height"], location["x"], location["x"] + size["width"]
        return top, bottom, left, right, size

    def get_screenshot(self):
        screenshot = self.browser.get_screenshot_as_png()
        return Image.open(BytesIO(screenshot))

    def get_gap(self, image1, image2):
        """
        对比两张图片的像素点，找到滑块要滑动的位置，返回滑块的滑动距离
        :return: 滑块的滑动距离
        """
        for i in range(LEFT, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    return i
        return LEFT

    def is_pixel_equal(self, image1, image2, x, y):
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        if abs(pixel1[0] - pixel2[0]) < THRESHOLD and abs(pixel1[1] - pixel2[1]) < THRESHOLD and abs(
                pixel1[2] - pixel2[2]) < THRESHOLD:
            return True
        else:
            return False

    def get_track(self, distance):
        """
        模拟用户验证行为，计算出移动距离
        :param distance: 滑块移动的距离
        :return: 加速与减速路径
        """
        distance += 20
        forward_tracks = []
        mid = distance * 4 / 5
        current = 0
        t = 0.2
        v = 0

        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3

            v0 = v
            v = v0 + a * t
            x = v0 * t + 0.5 * a * t * t
            current += x
            forward_tracks.append(round(x))

        backward_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]
        return {'forward_tracks': forward_tracks, 'backward_tracks': backward_tracks}

    def get_slider(self):
        return self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "geetest_slider_button")))

    def move_to_gap(self, slider, track) -> None:
        ActionChains(self.browser).click_and_hold(slider).perform()
        # 模拟往右滑动缺口并超出一段距离
        for x in track['forward_tracks']:
            ActionChains(self.browser).move_by_offset(
                xoffset=x, yoffset=0).perform()

        time.sleep(0.5)
        # 模拟往左返回滑动缺口
        for x in track['backward_tracks']:
            ActionChains(self.browser).move_by_offset(
                xoffset=x, yoffset=0).perform()

        ActionChains(self.browser).release().perform()

    def crack(self):
        self.open()
        button = self.get_geetest_button()
        button.click()  # 点击登录，弹出验证码
        print('点击登录，弹出验证码')
        time.sleep(1)
        image1 = self.get_geetest_image("bilibili1.png", True)  # 获取无缺口的验证码图片
        time.sleep(1)
        image2 = self.get_geetest_image("bilibili2.png", False)  # 获取有缺口的验证码图片
        print('获取验证码图片')
        gap = self.get_gap(image1, image2)
        track = self.get_track(gap - BORDER)
        slider = self.get_slider()
        self.move_to_gap(slider, track)  # 滑动滑块，进行验证
        time.sleep(3)
        if self.browser.current_url == 'https://www.bilibili.com/':
            print('登录成功')
        else:
            self.crack()


if __name__ == "__main__":
    crack = CrackGeeTest()
    crack.crack()
