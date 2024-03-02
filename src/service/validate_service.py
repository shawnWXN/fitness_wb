# -*- coding:utf-8 -*-
from jsonschema import validate

from common.const import CONST
from loggers.logger import logger


def validate_common_task_data(data: dict):
    arrival_fee_post_schema = {
        CONST.TYPE: CONST.OBJECT,
        CONST.ADDITIONAL_PROPERTIES: False,
        CONST.REQUIRED: [CONST.CATEGORY, CONST.API_NAME, CONST.SOURCE, CONST.UID, CONST.TASK_TYPE, CONST.TASK_DICT],
        CONST.PROPERTIES: {
            CONST.CATEGORY: {
                CONST.DESCRIPTION: "api类别",
                CONST.TYPE: CONST.STRING,
                CONST.MIN_LENGTH: 1,
                CONST.ENUM: CONST.CATEGORY_ENUM
            },
            CONST.API_NAME: {
                CONST.DESCRIPTION: "api名称",
                CONST.TYPE: CONST.STRING,
                CONST.MIN_LENGTH: 1
            },
            CONST.SOURCE: {
                CONST.DESCRIPTION: "调用方",
                CONST.TYPE: CONST.STRING,
                CONST.MIN_LENGTH: 1,
                CONST.ENUM: CONST.SOURCE_ENUM
            },
            CONST.UID: {
                CONST.DESCRIPTION: "调用方用户ID",
                CONST.TYPE: CONST.STRING,
                CONST.MIN_LENGTH: 1
            },
            CONST.TASK_TYPE: {
                CONST.DESCRIPTION: "任务类型",
                CONST.TYPE: CONST.STRING,
                CONST.MIN_LENGTH: 1,
                CONST.ENUM: CONST.TASK_TYPE_ENUM
            },
            CONST.TASK_DICT: {
                CONST.DESCRIPTION: "任务具体的数据",
                CONST.TYPE: CONST.OBJECT
            },
            CONST.INTERVAL: {
                CONST.DESCRIPTION: "loop任务指定的循环间隔(s)",
                CONST.TYPE: CONST.INTEGER
            },
            CONST.CALLBACK: {
                CONST.DESCRIPTION: "调用方指定的回调参数",
                CONST.TYPE: CONST.OBJECT,
                CONST.ADDITIONAL_PROPERTIES: True,
                CONST.REQUIRED: [CONST.URL],
                CONST.PROPERTIES: {
                    CONST.URL: {
                        CONST.DESCRIPTION: "回调url",
                        CONST.TYPE: CONST.STRING,
                        CONST.MIN_LENGTH: 1
                    }
                }
            }
        }
    }
    if not __validate_data(arrival_fee_post_schema, data):
        return False

    if data.get(CONST.TASK_TYPE) == CONST.LOOP and data.get(CONST.INTERVAL, 0) <= 0:
        logger.error(
            f"ValueError: {CONST.TASK_TYPE}={data.get(CONST.TASK_TYPE)} && {CONST.INTERVAL}={data.get(CONST.INTERVAL)}")
        return False

    return True


def __validate_data(schema, data):
    try:
        validate(data, schema)
        return True
    except Exception as e:
        logger.exception(str(e))
        return False
