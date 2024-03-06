# -*- coding: utf-8 -*-
import os
from dataclasses import dataclass


@dataclass
class _SETTING:
    MYSQL_URI: str = 'mysql://root:wang2702@120.78.190.176:28060/fitness_db'
    LOG_LEVEL: str = 'INFO'
    RETENTION: str = '14 days'

    def __init__(self):
        for attr, default_value in self.__class__.__dict__.items():
            if not attr.startswith('__') and not callable(getattr(self, attr)):
                env_value = os.environ.get(attr, default_value)
                setattr(self, attr, env_value)


SETTING = _SETTING()
