import base64
import inspect
import os.path
import re
import time
import typing
from functools import lru_cache, wraps
from io import BytesIO
from PIL import Image

import qrcode
import requests
from sanic.response import json as sanic_json
from sanic.request import Request

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


def page_num_size(request: Request):
    page_size = request.args.get(CONST.PAGE_SIZE)
    if page_size and page_size.isdigit():
        page_size = int(page_size)
        page_size = page_size if page_size <= 100 else 100
    else:
        page_size = 10

    page_num = request.args.get(CONST.PAGE_NUM)
    if page_num and page_num.isdigit():
        page_num = int(page_num) or 1
    else:
        page_num = 1

    return page_num, page_size


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
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    # 添加数据到 QR 码
    qr.add_data(s)
    qr.make(fit=True)

    # 创建 QR 码图像
    img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 打开 logo 文件
    # logo = Image.open('my_avatar.png')
    logo = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png'))

    # 计算 logo 的大小（这里我们设定 logo 大小为 QR 码的 1/4）
    logo_size = int(min(img_qr.size) / 5)

    # 重新设置 logo 的大小
    logo = logo.resize((logo_size, logo_size), Image.Resampling.BILINEAR)

    # 计算 logo 在 QR 码上的位置
    pos = ((img_qr.size[0] - logo_size) // 2, (img_qr.size[1] - logo_size) // 2)

    # 将 logo 粘贴到 QR 码上
    img_qr.paste(logo, pos)

    # 创建一个字节流来保存二维码图像
    byte_io = BytesIO()

    # 保存二维码图像到字节流，格式为PNG
    img_qr.save(byte_io, 'PNG')

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


def get_openid(request):
    real_id = request.headers.get('x-wx-openid') or None
    mock_id = request.headers.get('x-dev-openid') or None
    return mock_id or real_id if SETTING.DEV else real_id


def get_module_func(func: typing.Callable = None):
    if func is None:
        # 获取当前函数名
        current_function_name = inspect.currentframe().f_back.f_code.co_name
        # 获取当前模块名
        current_module_name = inspect.getmodule(inspect.currentframe().f_back).__name__
        # 行号
        line_no = inspect.currentframe().f_back.f_code.co_firstlineno

    else:
        # 获取传入函数的函数名
        current_function_name = func.__name__
        # 获取传入函数的模块名
        current_module_name = inspect.getmodule(func).__name__
        # 行号
        _, line_no = inspect.getsourcelines(func)

    return f'{current_module_name}:{line_no}:{current_function_name}'


class TokenBucketExceedError(Exception):
    pass


token_buckets = {}  # 使用字典作为内存存储


def token_bucket_limiter(openid, seconds: float = 1.5, capacity: int = 1,
                         exceed_handle: typing.Any = TokenBucketExceedError("Too many requests, please try again.")):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            key = openid + '@' + get_module_func(func)

            # 移除seconds秒前的请求记录
            if key in token_buckets:
                token_buckets[key] = [t for t in token_buckets[key] if t >= current_time - seconds]

            # 检查当前是否超过请求数量限制
            if len(token_buckets.get(key, [])) < capacity:
                token_buckets.setdefault(key, []).append(current_time)
                return func(*args, **kwargs)
            else:
                if callable(exceed_handle):
                    return exceed_handle()
                elif isinstance(exceed_handle, Exception):
                    raise exceed_handle
                else:
                    return exceed_handle

        return wrapper

    return decorator
