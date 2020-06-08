# coding: utf-8
# Author：houszhou
# Date ：2020/5/27 15:47
# Tool ：PyCharm
import subprocess
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from db_lib.to_db.change import run_change


def start_spider():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print('start_spider start')
    subprocess.Popen('scrapy crawlall')
    print('start_spider end')


def data_change():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print('data_change start')
    run_change()
    print('data_change end')


scheduler = BlockingScheduler()
scheduler.add_job(start_spider, 'cron', hour=19, minute=9)
scheduler.add_job(data_change, 'cron', hour=23, minute=16)
scheduler.start()
