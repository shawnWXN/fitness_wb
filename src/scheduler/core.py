# -*- coding:utf-8 -*-
import os
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler import events

from loggers.logger import logger


class _Scheduler:

    def __init__(self):
        self.job_defaults = {
            'coalesce': False,  # 不合并job
            'max_instances': 1  # 最大并发数
        }

        self.aps = None

    def add_job(self, *arg, **kw):
        self.aps.add_job(*arg, **kw)

    def run(self, loop):
        logger.info("Start Apscheduler. " + f'bound event_loop at PID[{os.getpid()}]' if loop else '')
        self.aps = AsyncIOScheduler(job_defaults=self.job_defaults, event_loop=loop)
        self.aps.add_listener(
            lambda e: logger.error(
                f'Job error: {str(e.exception)}, \n{"".join(traceback.format_tb(e.exception.__traceback__))}'),
            events.EVENT_JOB_ERROR)
        self.aps.start()

    def stop(self):
        self.aps.shutdown()
        logger.info("Apscheduler shutdown.")


aps = _Scheduler()
