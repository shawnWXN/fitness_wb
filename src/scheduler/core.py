# -*- coding:utf-8 -*-
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from loggers.logger import logger


class _Scheduler:

    def __init__(self):
        self.job_defaults = {
            'coalesce': False,  # 不合并job
            'max_instances': 1  # 最大并发数
        }

        self.aps = None

    def add(self, *arg, **kw):
        self.aps.add_job(*arg, **kw)

    def run(self, loop):
        logger.info("Start Apscheduler. " + f'bound event_loop at PID[{os.getpid()}]' if loop else '')
        self.aps = AsyncIOScheduler(job_defaults=self.job_defaults, event_loop=loop)
        self.aps.start()

    def stop(self):
        self.aps.shutdown()
        logger.info("Apscheduler shutdown.")


aps = _Scheduler()
