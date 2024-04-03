import base64
import inspect
import re
import time
import typing
from functools import lru_cache, wraps
from io import BytesIO

import qrcode
import requests
from sanic.response import json as sanic_json

from common.const import CONST
from loggers.logger import logger


def resp_success(resp_data: dict = None, **kwargs):
    resp_data = resp_data or {}
    result = {
        CONST.MESSAGE: CONST.SUCCESS.lower()
    }
    result.update(resp_data)
    result.update(kwargs)
    return sanic_json(result)


def resp_failure(status_code, reason, resp_data: dict = None, print_log: bool = True, **kwargs):
    resp_data = resp_data or {}
    result = {
        CONST.MESSAGE: reason
    }
    result.update(resp_data)
    result.update(kwargs)
    if print_log:
        logger.error(f'{result}, {status_code}')
    return sanic_json(result, status=status_code)


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


@lru_cache()
def str2base64(s: str) -> str:
    """
    生成字符串对应的图片（base64字符串）
    """
    qr_img = qrcode.make(s)

    # 创建一个字节流来保存二维码图像
    byte_io = BytesIO()

    # 保存二维码图像到字节流，格式为PNG
    qr_img.save(byte_io, 'PNG')

    # 将字节流的内容转换为Base64编码的字符串
    base64_str = base64.b64encode(byte_io.getvalue()).decode('utf-8')

    # 创建一个完整的Base64编码的图像数据字符串
    base64_image = 'data:image/png;base64,' + base64_str

    # 打印或返回Base64编码的图像数据字符串
    return base64_image


def days_bill_description(limit_days):
    match limit_days:
        case 30:
            return '月卡'
        case 90:
            return '季卡'
        case 180:
            return '半年卡'
        case 365:
            return '年卡'
        case _:
            assert False, "Invalid limit_days"


def retry(
        max_retry: int = 3,
        name: str = None,
        sleep: int = 2,
        sleep_strategy: typing.Callable = None,
        can_be_none: bool = True
):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal name
            if not name:
                name = get_module_func(func)
            retry_turn = 0
            while True:
                try:
                    return_value = func(*args, **kwargs)
                    if not can_be_none and return_value is None:
                        raise Exception('NoneResultError, func:{} returns None'.format(name))
                    return return_value
                except Exception as e:
                    exec_info = f'{e.__class__.__name__}<{str(e)}>'
                    logger.warning(
                        'func:{}, failed:{}, args:{}, kwargs:{}, retry:{}/{}...'.format(name, exec_info, args, kwargs,
                                                                                        retry_turn, max_retry))
                    retry_turn += 1

                    if max_retry and retry_turn > max_retry:
                        break

                    sleep_seconds = sleep_strategy(retry_turn) if sleep_strategy else sleep
                    logger.warning('func:{} next retry after {} seconds'.format(name, sleep_seconds))
                    time.sleep(sleep_seconds)

            raise Exception('MaxRetryError, func:{}, failed:{}, retry turn: {}'.format(name, exec_info, retry_turn))

        return wrapper

    return decorate


@retry(max_retry=6)
def requests_retry(method, url, **kwargs) -> requests.Response:
    """发送GET请求并返回响应"""
    kwargs['timeout'] = 300
    response = requests.request(method, url, **kwargs)
    if 400 <= response.status_code < 500:
        return response
    response.raise_for_status()  # 如果响应错误（例如404 Not Found）将引发异常
    return response


def get_module_func(func: typing.Callable = None):
    if func is None:
        # 获取当前函数名
        current_function_name = inspect.currentframe().f_back.f_code.co_name
        # 获取当前模块名
        current_module_name = inspect.getmodule(inspect.currentframe().f_back).__name__
    else:
        # 获取传入函数的函数名
        current_function_name = func.__name__
        # 获取传入函数的模块名
        current_module_name = inspect.getmodule(func).__name__

    return f'{current_module_name}:{current_function_name}'
