import win32api
import win32gui

win32api.ShellExecute(1, 'open', r'C:\Program Files (x86)\Tencent\WeChat\WeChat.exe', '', '', 1)
wechat = win32gui.FindWindow(None, '微信')
menu = win32gui.GetMenu(wechat)
print(menu)
