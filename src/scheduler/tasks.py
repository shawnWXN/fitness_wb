import typing
from datetime import datetime

from common.enum import OrderStatusEnum
from loggers.logger import logger
from orm.model import OrderModel, CourseModel
from scheduler.core import aps


async def expire_order():
    modified_count = await OrderModel.filter(expire_time__lt=datetime.now()) \
        .update(status=OrderStatusEnum.EXPIRED.value)

    if modified_count:
        logger.info(f"{modified_count}'s Order expired")


async def add_limit_counts():
    objs: typing.List[OrderModel] = await OrderModel.all()
    for obj in objs:
        course = await CourseModel.get_or_none(id=obj.course_id)
        if not course:
            logger.error(f"not found course[{obj.course_id}]")
        else:
            obj.limit_counts = course.limit_counts
            await obj.save()
            logger.info(f"found course[{obj.course_id}], limit_counts: {obj.limit_counts}")


async def run_tasks():
    aps.add_job(expire_order, 'cron', hour='0', minute='1')
    # aps.add_job(add_limit_counts)
