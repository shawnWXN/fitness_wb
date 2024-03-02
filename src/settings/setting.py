# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass

from loggers.logger import logger


@dataclass
class _SETTING:
    MYSQL_URI: str
    LOG_LEVEL: str
    RETENTION: str

    def __init__(self):
        self.MYSQL_URI = os.environ.get("MYSQL_URI", "localhost")
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
        self.RETENTION = os.environ.get("RETENTION", "14 days")
        for k, v in os.environ.items():
            logger.error(f'{k}: {v}')


SETTING = _SETTING()
