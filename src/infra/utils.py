import hashlib
import multiprocessing
import platform
import re

from sanic.response import json as sanic_json

from common.const import CONST
from loggers.logger import logger
from settings.setting import SETTING


def resp_success(resp_data: dict = None, **kwargs):
    resp_data = resp_data or {}
    result = {
        CONST.MESSAGE: CONST.SUCCESS.lower()
    }
    result.update(resp_data)
    result.update(kwargs)
    return sanic_json(result)


def resp_failure(error_code, reason, resp_data: dict = None, print_log: bool = True, **kwargs):
    resp_data = resp_data or {}
    result = {
        CONST.MESSAGE: CONST.FAILURE.lower(),
        CONST.ERROR_CODE: error_code,
        CONST.REASON: reason
    }
    result.update(resp_data)
    result.update(kwargs)
    if print_log:
        logger.error(result)
    return sanic_json(result)


def number_of_workers():
    if platform.system().lower() == 'linux':
        return (multiprocessing.cpu_count() * 2) + 1
    return 1


def md5(str_value):
    m = hashlib.md5()
    m.update(str_value.encode('utf8'))
    return m.hexdigest()


def check_token(data: dict):
    timestamp = data.get(CONST.TIMESTAMP, "")
    outer_token = data.get(CONST.TOKEN, "")
    inner_token = md5(SETTING.TOKEN_SEED + timestamp)
    if outer_token != inner_token:
        logger.warning(
            f"outer_token: {outer_token}, inner_token: {inner_token} ref: md5(token_seed={SETTING.TOKEN_SEED}, timestamp={timestamp})")
        return False
    return True


def snake2camel(snake: str, start_lower: bool = False) -> str:
    """
    Converts a snake_case string to camelCase.

    The `start_lower` argument determines whether the first letter in the generated camelcase should
    be lowercase (if `start_lower` is True), or capitalized (if `start_lower` is False).
    """
    camel = snake.title()
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)
    if start_lower:
        camel = re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)
    return camel


def camel2snake(camel: str) -> str:
    """
    Converts a camelCase string to snake_case.
    """
    snake = re.sub(r"([a-zA-Z])([0-9])", lambda m: f"{m.group(1)}_{m.group(2)}", camel)
    snake = re.sub(r"([a-z0-9])([A-Z])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    return snake.lower()
