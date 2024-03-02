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


def add_rotating_file_handler(logger, file_name, level=None):
    handler = RotatingFileHandler(
        file_name, maxBytes=CONST.MAX_BACK_FILE_SIZE, backupCount=CONST.MAX_BACK_FILE_NUM, encoding=CONST.UTF_8)

    if level:
        handler.setLevel(level)

    handler.setFormatter(logging.Formatter('[%(asctime)s]-' + get_logger_format()))
    logger.addHandler(handler)


def add_stream_handler(logger):
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(colorlog.ColoredFormatter("%(log_color)s" + get_logger_format()))
    logger.addHandler(stream_handler)


def init_logger(log_level):
    logger = logging.getLogger(CONST.SYSTEM_NAME + '_' + CONST.SUB_SYSTEM_NAME)
    add_rotating_file_handler(logger, LOG_PATH / get_logger_file_name('.error'), level=logging.ERROR)
    add_rotating_file_handler(logger, LOG_PATH / get_logger_file_name())
    add_stream_handler(logger)
    logger.setLevel(log_level)
    logger.propagate = False
    return logger


logger = init_logger(logging.INFO)

# import sys
# from pathlib import Path
#
# import log_collector  # noqa
# from loguru import logger as _logger
#
# from settings.setting import SETTING
#
# # 创建日志目录
# LOG_PATH = Path.cwd().parent / 'logs'
# LOG_PATH.mkdir(parents=True, exist_ok=True)
# LOG_FORMAT = "{level:<8}|{module}.{function}:{line} - {message}"
# FILE_LOG_CONF = dict(format='{time:YYYY-MM-DD HH:mm:ss,SSS}|' + LOG_FORMAT, encoding='utf-8',
#                      retention=SETTING.RETENTION, rotation='00:00', mode='a', enqueue=True)
#
# _logger.configure(
#     handlers=[
#         dict(sink=sys.stdout, format=LOG_FORMAT, level=SETTING.LOG_LEVEL.upper()),
#         dict(sink=LOG_PATH / '{time:YYYYMMDD}.log', level='INFO', **FILE_LOG_CONF),
#         dict(sink=LOG_PATH / '{time:YYYYMMDD}.error.log', level='ERROR', **FILE_LOG_CONF)
#     ])
# log_collector.initializer.start(_logger,
#                                 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=1b41e2cd-32c2-4fdc-a8b0-ee4873399def',
#                                 service_name=CONST.SYSTEM_APP_NAME)
# logger = _logger
