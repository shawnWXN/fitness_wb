import copy
import re
import typing
from datetime import datetime

from jsonschema import validate, ValidationError, SchemaError

from common.const import CONST
from common.enum import BillTypeEnum, OrderStatusEnum, StaffRoleEnum, ExpenseStatusEnum, ScanSceneEnum
from loggers.logger import logger
from service.wx_openapi import phone_via_code

userprofile_update_schema = {
    "type": "object",
    "properties": {
        "phone": {
            "type": ["string", "null"],
            "title": "手机号",
            "minLength": 1
        },
        "nickname": {
            "type": ["string", "null"],
            "title": "微信昵称",
            "minLength": 1
        },
        "avatar": {
            "type": ["string", "null"],
            "title": "头像",
            "minLength": 1
        },
        "subscribe_incr": {
            "type": "integer",
            "title": "订阅消息增量",
            "minimum": 1
        }
    },
    "minProperties": 1
}

user_update_schema = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "title": "ID 编号",
            "minimum": 1
        },
        "staff_roles": {
            "type": ["array", "null"],
            "items": {
                "type": "integer",
                "enum": StaffRoleEnum.iter.value
            },
            "title": "账号权限列表",
            "minItems": 0,
            "maxItems": len(StaffRoleEnum.iter.value),
            "uniqueItems": True
        },
        "name_zh": {
            "type": ["string", "null"],
            "title": "中文姓名",
            "minLength": 1
        }
    },
    "required": [
        "id"
    ]
}

course_create_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {
            "type": "string",
            "title": "课程名",
            "minLength": 1
        },
        "intro": {
            "type": "string",
            "title": "课程简介",
            "minLength": 1
        },
        # "coach_id": {
        #     "type": "integer",
        #     "title": "教练编号ID",
        #     "minimum": 1,
        # },
        "thumbnail": {
            "type": "string",
            "title": "课程封面图",
            "minLength": 1
        },
        "description": {
            "type": ["string", "null"],
            "title": "课程详细文字",
            # "minLength": 1
        },
        "desc_images": {
            "type": ["array", "null"],
            "items": {
                "type": "string",
                "minLength": 1
            },
            "title": "课程详细图片",
            "minItems": 0,
            "maxItems": 3,
            "uniqueItems": True
        },
        "bill_type": {
            "type": "string",
            "enum": BillTypeEnum.iter.value,
            "title": "计费类型"
        },
        "limit_days": {
            "type": "integer",
            "enum": [
                0, 30, 90, 180, 365
            ],
            # "minimum": 0,
            # "maximum": 1000,
            # "exclusiveMaximum": 1000,
            "title": "有效天数"
        },
        "limit_counts": {
            "type": "integer",
            "minimum": 0,
            "maximum": 10000,
            "exclusiveMaximum": 10000,
            "title": "有效次数"
        }
    },
    "required": [
        "name",
        "intro",
        # "coach_id",
        "thumbnail",
        "bill_type"
    ]
}

order_create_schema = {
    "type": "object",
    "properties": {
        "member_id": {
            "type": "integer",
            "minimum": 1,
            "title": "会员ID"
        },
        "course_id": {
            "type": "integer",
            "minimum": 1,
            "title": "课程ID"
        },
        "amount": {
            "type": "integer",
            "minimum": 0,
            "title": "订单金额",
        },
        "receipt": {
            "type": "string",
            "title": "付款截图",
            "minLength": 1
        },
        "contract": {
            "type": ["string", "null"],
            "title": "合同文件",
            "minLength": 1
        }
    },
    "required": [
        "member_id",
        "course_id",
        "amount",
        # "receipt",
    ]
}

order_update_schema_first = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "minimum": 1,
            "title": "ID 编号"
        },
        "status": {
            "type": "string",
            "enum": [
                OrderStatusEnum.ACTIVATED.value,
                OrderStatusEnum.REFUND.value,
            ],
            "title": "订单状态"
        }
    },
    "required": [
        "id",
        "status"
    ]
}

order_update_schema_part = {  # 订单更新schema片段
    "type": "object",
    "properties": {
        "course_id": {
            "type": ["integer", "null"],
            "minimum": 1,
            "title": "课程ID"
        },
        "surplus_counts": {
            "type": ["integer", "null"],
            "minimum": 1,
            "maximum": 10000,
            "exclusiveMaximum": 10000,
            "title": "剩余次数"
        },
        "limit_counts": {
            "type": ["integer", "null"],
            "minimum": 1,
            "maximum": 10000,
            "exclusiveMaximum": 10000,
            "title": "有效次数"
        },
        "expire_time": {
            "type": ["string", "null"],
            "pattern": r"(20[0-9]{2}|2[1-9][0-9]{2})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])",
            "title": "到期时间"
        },
        "amount": {
            "type": ["integer", "null"],
            "minimum": 0,
            "title": "订单金额",
        },
        "receipt": {
            "type": ["string", "null"],
            "title": "付款截图",
            "minLength": 1
        },
        "contract": {
            "type": ["string", "null"],
            "title": "合同文件",
            "minLength": 1
        }
    }
}

order_comment_create_schema = {
    "type": "object",
    "properties": {
        "order_no": {
            "type": "string",
            "title": "订单编号",
            "minLength": 1,
        },
        "comment": {
            "type": "string",
            "title": "备注内容",
            "minLength": 1
        }
    },
    "required": [
        "order_no",
        "comment"
    ]
}

expense_update_schema = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "title": "ID 编号",
            "minimum": 1,
        },
        "status": {
            "type": "string",
            "title": "状态",
            "enum": [
                ExpenseStatusEnum.REJECT.value,
                ExpenseStatusEnum.ACTIVATED.value,
                ExpenseStatusEnum.FREE.value
            ],
        }
    },
    "required": [
        "id",
        "status"
    ]
}

qrcode_create_schema = {
    "type": "object",
    "properties": {
        "scene": {
            "type": "string",
            "title": "场景值",
            "enum": ScanSceneEnum.iter.value,
        },
        "uuid": {
            "type": "string",
            "title": "唯一标识",
            "minLength": 1
        }
    },
    "required": [
        "scene",
        "uuid"
    ]
}


def validate_order_expense_get_args(request,
                                    status_enum: typing.Type[OrderStatusEnum] | typing.Type[ExpenseStatusEnum]):
    status: str = request.args.get(CONST.STATUS)
    create_date_start: str = request.args.get(CONST.START_DT)
    create_date_end: str = request.args.get(CONST.END_DT)

    # 要求1: 校验status
    if status and set(status.split(',')) - set(status_enum.iter.value):
        return False, f"`状态` 不在指定范围"

    # 要求2: 校验日期格式
    request.ctx.args = dict()
    date_format = "%Y-%m-%d"
    try:
        if create_date_start:
            # 尝试将字符串转换为日期对象
            start_date = datetime.strptime(create_date_start, date_format)
            request.ctx.args[CONST.START_DT] = start_date  # 这里改str为datetime.datetime
        if create_date_end:
            # 尝试将字符串转换为日期对象
            end_date = datetime.strptime(create_date_end, date_format)
            request.ctx.args[CONST.END_DT] = end_date  # 这里改str为datetime.datetime
    except ValueError:
        # 如果转换失败，说明日期格式不正确
        return False, f"`开始时间`或`结束时间`模式匹配失败"

    # 要求3: 校验create_date_end是否大于等于create_date_start
    if create_date_start and create_date_end:
        if end_date < start_date:  # noqa
            return False, f"`结束时间`不得小于`开始时间`"

    return True, None


def validate_userprofile_update_data(data: dict) -> typing.Tuple[bool, str]:
    rst, err_msg = __validate_data(data, userprofile_update_schema)
    if not rst:
        return rst, err_msg

    if data.get('phone') and not re.match(r'^1\d{10}$', data.get('phone')):  # FIXME 手机号正则可能有问题
        data['phone'] = phone_via_code(data.get('phone'))  # 用code置换手机号

    return True, ''


def validate_user_update_data(data: dict) -> typing.Tuple[bool, str]:
    return __validate_data(data, user_update_schema)


def validate_course_create_data(data: dict) -> typing.Tuple[bool, str]:
    rst, err_msg = __validate_data(data, course_create_schema)
    if not rst:
        return rst, err_msg

    # if any([data.get('limit_days'), data.get('limit_counts')]) and not data.get('bill_type'):
    #     return False, f"miss bill_type when limit_days or limit_counts exists"

    if data.get("bill_type") == BillTypeEnum.DAY.value and not data.get('limit_days'):
        return False, f"包时课程需填写`有效天数`"

    if data.get("bill_type") == BillTypeEnum.COUNT.value and not data.get('limit_counts'):
        return False, f"计次课程需填写`有效次数`"

    return True, ''


def validate_course_update_data(data: dict) -> typing.Tuple[bool, str]:
    course_update_schema = copy.deepcopy(course_create_schema)
    course_update_schema['properties']['id'] = {
        "type": "integer",
        "title": "ID 编号",
        "minimum": 1,
    }
    course_update_schema['required'] = ['id']
    course_update_schema['minProperties'] = 2
    # 下面与新增时一致
    rst, err_msg = __validate_data(data, course_update_schema)
    if not rst:
        return rst, err_msg

    # if any([data.get('limit_days'), data.get('limit_counts')]) and not data.get('bill_type'):
    #     return False, f"miss bill_type when limit_days or limit_counts exists"

    if data.get("bill_type") == BillTypeEnum.DAY.value and not data.get('limit_days'):
        return False, f"包时课程需填写`有效天数`"

    if data.get("bill_type") == BillTypeEnum.COUNT.value and not data.get('limit_counts'):
        return False, f"计次课程需填写`有效次数`"

    return True, ''


def validate_order_create_data(data: dict) -> typing.Tuple[bool, str]:
    return __validate_data(data, order_create_schema)


def validate_order_update_data(data: dict) -> typing.Tuple[bool, str]:
    rst, err_msg = __validate_data(data, order_update_schema_first)
    if not rst:
        return rst, err_msg

    if data.get("status") == OrderStatusEnum.ACTIVATED.value:
        return __validate_data(data, order_update_schema_part)
    else:
        [data.pop(k) for k in list(data.keys()) if k not in ("id", "status")]

    return True, ''


def validate_order_comment_create_data(data: dict) -> typing.Tuple[bool, str]:
    return __validate_data(data, order_comment_create_schema)


def validate_expense_update_data(data: dict) -> typing.Tuple[bool, str]:
    return __validate_data(data, expense_update_schema)


def validate_qrcode_create_data(data: dict) -> typing.Tuple[bool, str]:
    return __validate_data(data, qrcode_create_schema)


def __parse_error_msg(e: ValidationError, schema: dict):
    if e.absolute_schema_path.count(CONST.ANYOF) or e.absolute_schema_path.count(
            CONST.ONEOF) or e.absolute_schema_path.count(CONST.ALLOF):
        k = ''
        for k in e.absolute_schema_path:
            # 因为模式组合的validate错误，固定取第一个模式，无法表述真实错误原因
            # 故如需自定义err_msg，请把err_msg与模式组合关键字（oneOf, anyOf, allOf）写在同一级
            if k in (CONST.ANYOF, CONST.ONEOF, CONST.ALLOF):
                break
            schema = schema.get(k)
        description = (schema.get(CONST.DESCRIPTION) or schema.get(CONST.TITLE)) or ".".join(map(str, e.absolute_path))
        err_msg = schema.get(CONST.ERR_MSG, {}).get(k, '')
        if err_msg:
            err_msg = err_msg if err_msg.startswith(description) else f'`{description}`{err_msg}'
        else:
            err_msg = f'`{description}` 不符合{k}模式组合'

    else:
        description = (e.schema.get(CONST.DESCRIPTION) or e.schema.get(CONST.TITLE)) or ".".join(
            map(str, e.absolute_path))
        err_msg = e.schema.get(CONST.ERR_MSG, {}).get(e.validator, '')
        if err_msg:
            err_msg = err_msg if err_msg.startswith(description) else f'`{description}`{err_msg}'
        else:
            if e.validator == CONST.REQUIRED:
                err_msg = f"`{description}` 缺少必要参数" if description else "缺少必要参数"
            elif e.validator == CONST.ADDITIONAL_PROPERTIES:
                err_msg = f"`{description}` 含有非法参数" if description else "含有非法参数"
            elif e.validator in (CONST.MAX_PROPERTIES, CONST.MIN_PROPERTIES):
                err_msg = f"`{description}` 参数数量错误" if description else "参数数量错误"
            elif e.validator in (CONST.MAX_LENGTH, CONST.MIN_LENGTH):
                err_msg = f"`{description}` 字符长度错误"
            elif e.validator in (CONST.MINITEMS, CONST.MAXITEMS):
                err_msg = f"`{description}` 数组长度错误"
            elif e.validator in (CONST.MINIMUM, CONST.MAXIMUM, CONST.EXCLUSIVE_MINIMUM, CONST.EXCLUSIVE_MAXIMUM):
                err_msg = f"`{description}` 数值范围错误"
            elif e.validator == CONST.TYPE:
                err_msg = f"`{description}` 参数类型错误"
            elif e.validator == CONST.ENUM:
                err_msg = f"`{description}` 不在指定范围"
            elif e.validator == CONST.SCHEMA_CONST:
                err_msg = f"`{description}` 不等于预设值"
            elif e.validator == CONST.PATTERN:
                err_msg = f"`{description}` 模式匹配失败"

    return err_msg


def __validate_data(data: dict, schema: dict) -> typing.Tuple[bool, str]:
    rst = True
    err_msg = ''
    try:
        validate(data, schema)
    except SchemaError as e:
        logger.exception("schema invalid:{}".format(str(e)))
        rst, err_msg = False, e.message

    except ValidationError as e:
        logger.exception("validate error:{}".format(e.message))
        e.schema_path.insert(-1, CONST.ERR_MSG)
        rst, err_msg = False, __parse_error_msg(e, schema) or e.message

    except Exception as e:
        logger.exception(str(e))
        rst, err_msg = False, str(e)

    return rst, err_msg
