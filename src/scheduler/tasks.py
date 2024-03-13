import time
from datetime import datetime, timedelta

from scheduler.core import aps


def func1():
    print(time.time())
    aps.add_job(func1, 'date', run_date=datetime.now() + timedelta(seconds=3))


def run_tasks():
    ...
    # aps.add_job(func1, 'date', run_date=datetime.now() + timedelta(seconds=3))
