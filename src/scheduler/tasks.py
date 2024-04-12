import time
from datetime import datetime, timedelta

from loggers.logger import logger
from scheduler.core import aps


def func1():
    logger.info(time.time())
    aps.add_job(func1, 'date', run_date=datetime.now() + timedelta(seconds=30))


def run_tasks():
    aps.add_job(func1, 'date', run_date=datetime.now() + timedelta(seconds=30))
