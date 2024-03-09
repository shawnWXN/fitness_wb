import copy
import typing

from jsonschema import validate, ValidationError, SchemaError

from common.const import CONST
from common.enum import BillTypeEnum, GenderEnum
from loggers.logger import logger

userprofile_update_schema = {
    "type": "object",
    "properties": {
        "phone": {
            "type": ["string", "null"],
            "title": "手机号",
            "pattern": "^1\\d{10}$"
        },
        "nickname": {
            "type": ["string", "null"],
            "title": "名称",
            "minLength": 1
        },
        "avatar": {
            "type": ["string", "null"],
            "title": "头像",
            "minLength": 1
        },
        "gender": {
            "type": "string",
            "title": "性别",
            "enum": [  # tips 指定enum后，type列表不再支持null
                GenderEnum.UNKNOWN.value,
                GenderEnum.FEMALE.value,
                GenderEnum.MALE.value,
            ]
        }
    }
}

course_create_schema = {
    "type": "object",
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
        "coach_id": {
            "type": "integer",
            "title": "教练编号ID",
            "minimum": 1,
        },
        "thumbnail": {
            "type": "string",
            "title": "课程封面图",
            "minLength": 1
        },
        "bill_type": {
            "type": "string",
            "enum": [
                BillTypeEnum.DAY.value,
                BillTypeEnum.COUNT.value
            ],
            "title": "计费类型"
        },
        "description": {
            "type": ["string", "null"],
            "title": "课程详细文字",
            "minLength": 1
        },
        "desc_images": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1
            },
            "title": "课程详细图片",
            "maxItems": 3,
            "minItems": 0
        },
        "limit_days": {
            "type": ["integer", "null"],
            "minimum": 1,
            "maximum": 1000,
            "exclusiveMaximum": 1000,
            "title": "有效天数"
        },
        "limit_counts": {
            "type": ["integer", "null"],
            "minimum": 1,
            "maximum": 1000,
            "exclusiveMaximum": 1000,
            "title": "有效次数"
        }
    },
    "required": [
        "name",
        "intro",
        "coach_id",
        "thumbnail",
        "bill_type"
    ]
}


def validate_userprofile_update_data(data: dict) -> typing.Tuple[bool, str]:
    return __validate_data(data, userprofile_update_schema)


def validate_course_create_data(data: dict) -> typing.Tuple[bool, str]:
    rst, err_msg = __validate_data(data, course_create_schema)
    if not rst:
        return rst, err_msg

    if data.get("bill_type") == BillTypeEnum.DAY.value and not data.get('limit_days'):
        return False, f"miss limit_days when bill_type='{BillTypeEnum.DAY.value}'"

    if data.get("bill_type") == BillTypeEnum.COUNT.value and not data.get('limit_counts'):
        return False, f"miss limit_counts when bill_type='{BillTypeEnum.COUNT.value}'"

    return True, ''


def validate_course_update_data(data: dict) -> typing.Tuple[bool, str]:
    course_update_schema = copy.deepcopy(course_create_schema)
    course_update_schema['properties']['id'] = {
        "type": "integer",
        "title": "ID 编号",
        "minimum": 1,
    }
    course_update_schema['required'].append('id')
    # 下面与新增时一致
    rst, err_msg = __validate_data(data, course_update_schema)
    if not rst:
        return rst, err_msg

    if data.get("bill_type") == BillTypeEnum.DAY.value and not data.get('limit_days'):
        return False, f"miss limit_days when bill_type='{BillTypeEnum.DAY.value}'"

    if data.get("bill_type") == BillTypeEnum.COUNT.value and not data.get('limit_counts'):
        return False, f"miss limit_counts when bill_type='{BillTypeEnum.COUNT.value}'"

    return True, ''


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
        description = (schema.get(CONST.DESCRIPTION) or schema.get(CONST.TITLE)) or ".".join(map(str, e.absolute_path))
        err_msg = e.schema.get(CONST.ERR_MSG, {}).get(e.validator, '')
        if err_msg:
            err_msg = err_msg if err_msg.startswith(description) else f'`{description}`{err_msg}'
        else:
            if e.validator == CONST.REQUIRED:
                err_msg = f"`{description}` 缺少必要参数"
            elif e.validator == CONST.ADDITIONAL_PROPERTIES:
                err_msg = f"`{description}` 含有非法参数"
            elif e.validator in (CONST.MAX_PROPERTIES, CONST.MIN_PROPERTIES):
                err_msg = f"`{description}` 参数数量有误"
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
                err_msg = f"`{description}` 正则匹配失败"

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
