import re
from functools import lru_cache

import qrcode
from io import BytesIO
import base64

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
