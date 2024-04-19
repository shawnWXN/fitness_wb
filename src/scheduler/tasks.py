from datetime import datetime

from common.enum import OrderStatusEnum
from loggers.logger import logger
from orm.model import OrderModel
from scheduler.core import aps


async def expire_order():
    modified_count = await OrderModel.filter(expire_time__lt=datetime.now()) \
        .update(status=OrderStatusEnum.EXPIRED.value)

    if modified_count:
        logger.info(f"{modified_count}'s Order expired")


async def run_tasks():
    aps.add_job(expire_order, 'cron', hour='0', minute='1')
