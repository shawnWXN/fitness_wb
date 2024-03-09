import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog

from common.const import CONST

# 创建日志目录
LOG_PATH = Path.cwd().parent / 'logs'
LOG_PATH.mkdir(parents=True, exist_ok=True)


def get_logger_file_name(prefix=""):
    return CONST.SYSTEM_NAME + '_' + CONST.SUB_SYSTEM_NAME + prefix + '.log'


def get_logger_format() -> str:
    fmt = '[%(levelname)s]'
    fmt += '-[%(process)d]'
    fmt += '-[%(threadName)s]'
    fmt += '-[%(thread)d]'
    fmt += '-[%(filename)s:%(lineno)s]'
    fmt += ' # %(message)s'
    return fmt


def add_rotating_file_handler(_log, file_name, level=None):
    handler = RotatingFileHandler(
        file_name, maxBytes=CONST.MAX_BACK_FILE_SIZE, backupCount=CONST.MAX_BACK_FILE_NUM, encoding=CONST.UTF_8)

    if level:
        handler.setLevel(level)

    handler.setFormatter(logging.Formatter('[%(asctime)s]-' + get_logger_format()))
    _log.addHandler(handler)


def add_stream_handler(_log):
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s" + get_logger_format()))
    _log.addHandler(stream_handler)


def init_logger(log_level):
    _log = logging.getLogger(CONST.SYSTEM_NAME + '_' + CONST.SUB_SYSTEM_NAME)
    add_rotating_file_handler(_log, LOG_PATH / get_logger_file_name('.error'), level=logging.ERROR)
    add_rotating_file_handler(_log, LOG_PATH / get_logger_file_name())
    add_stream_handler(_log)
    _log.setLevel(log_level)
    _log.propagate = False
    return _log


logger = init_logger(logging.INFO)


def get_other_logger_format(module_name: str):
    fmt = '[%(asctime)s]'
    fmt += '-[%(levelname)s]'
    fmt += '-[%(process)d]'
    fmt += f'-[{module_name.title()}]'
    fmt += '-[%(thread)d]'
    fmt += '-[%(filename)s:%(lineno)s]'
    fmt += ' # %(message)s'
    return fmt


def add_other_rotating_file_handler(_log, module_name: str, file_name, level=None):
    handler = RotatingFileHandler(
        file_name, maxBytes=CONST.MAX_BACK_FILE_SIZE, backupCount=CONST.MAX_BACK_FILE_NUM, encoding=CONST.UTF_8)

    if level:
        handler.setLevel(level)

    handler.setFormatter(logging.Formatter(get_other_logger_format(module_name)))
    _log.addHandler(handler)


def add_other_stream_handler(_log, module_name: str):
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s" + get_other_logger_format(module_name)))
    _log.addHandler(stream_handler)


def init_other_logger(log_level, module_name: str):
    _log = logging.getLogger(module_name)
    add_other_rotating_file_handler(_log, module_name, LOG_PATH / get_logger_file_name('.error'), level=logging.ERROR)
    add_other_rotating_file_handler(_log, module_name, LOG_PATH / get_logger_file_name())
    add_other_stream_handler(_log, module_name)
    _log.setLevel(log_level)
    _log.propagate = False
    return _log


schedule_log = init_other_logger(logging.DEBUG, 'apscheduler')
# db_log = init_other_logger(logging.DEBUG, 'tortoise.db_client')
