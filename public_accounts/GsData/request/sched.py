from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from QingBo import QBO


def job():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    qb = QBO()
    qb.top_ten()


# BlockingScheduler
scheduler = BlockingScheduler()
scheduler.add_job(job, 'cron', hour=15, minute=3)
scheduler.start()
