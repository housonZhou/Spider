from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
import smtplib


class QQEmail:
    def __init__(self, from_addr, to_addr, password):
        self.title = '请登录微信扫描二维码'
        self.from_addr = from_addr
        self.password = password
        self.to_addr = to_addr
        self.smtp_server = 'smtp.qq.com'
        self.msg = MIMEMultipart()
        self.server = smtplib.SMTP(self.smtp_server, 25)

    def insert_img(self, img_path):
        body = '<html><body><h1>{}</h1><p><img src="cid:0"></p></body></html>'.format(self.title)
        self.msg.attach(MIMEText(body, 'html', 'utf-8'))
        mime = MIMEBase('image', 'png', filename='test.png')
        mime.add_header('Content-Disposition', 'attachment', filename='test.png')
        mime.add_header('Content-ID', '<0>')
        mime.add_header('X-Attachment-Id', '0')
        mime.set_payload(open(img_path, 'rb').read())
        encoders.encode_base64(mime)
        self.msg.attach(mime)

    def send(self):
        self.msg['From'] = _format_addr('<%s>' % self.from_addr)  # 发件人
        self.msg['To'] = _format_addr('<%s>' % self.to_addr)  # 收件人
        self.msg['Subject'] = Header(self.title, 'utf-8').encode()
        self.server.set_debuglevel(1)
        self.server.login(self.from_addr, self.password)
        self.server.sendmail(self.from_addr, [self.to_addr], self.msg.as_string())

    def __del__(self):
        self.server.quit()


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


if __name__ == '__main__':
    img = r'C:\Users\17337\houszhou\data\SpiderData\微信公众号\登陆二维码.png'
    account = '1733776802@qq.com'
    key = ''
    mail = QQEmail(account, account, key)
    mail.insert_img(img)
    mail.send()
