import pytz
import typing
from datetime import datetime, timedelta

from common.const import CONST
from common.enum import OrderStatusEnum, BillTypeEnum
from loggers.logger import logger
from orm.model import OrderModel, UserModel
from orm.user_orm import identifier_user_map
from scheduler.core import aps
from service.wx_openapi import subscribe_send


async def expire_order():
    modified_count = await OrderModel.filter(expire_time__lt=datetime.now()) \
        .update(status=OrderStatusEnum.EXPIRED.value)

    if modified_count:
        logger.info(f"{modified_count}'s Order expired")


async def order_notice():
    """
    1. 没有提醒过，且状态=active的订单
    2. 今日+四天 > expire_time 或者 剩余三次
    """
    now_dt = datetime.now(pytz.timezone('Asia/Shanghai'))
    query = await OrderModel.filter(
        notified=CONST.FALSE_STATUS, status=OrderStatusEnum.ACTIVATED.value
    ).all()

    # 单人多个订单即将过期，只提醒一次且用老订单的信息：剩余x课时（x天后过期）、课程名、下单日期、订单编号。
    user_notice_dict = {}
    for order in query:
        order: OrderModel

        if order.bill_type == BillTypeEnum.DAY and order.expire_time < (now_dt + timedelta(days=3)):
            delta_days = (order.expire_time - now_dt).days + 1
            phrase1 = '今日过期' if delta_days == 1 else f'{delta_days}天后过期'

        elif order.bill_type == BillTypeEnum.COUNT and order.limit_counts <= 2:
            phrase1 = f'剩余{order.limit_counts}课时'

        else:
            continue

        if order.member_id in user_notice_dict:
            logger.warning(
                f'{order.member_name} {order.course_name}[{order.create_time.strftime("%y年%m月%d日 %H:%M")}]'
                f' {phrase1} will continue.')

        user_notice_dict.setdefault(order.member_id, {
            "order_ids": [order.id],  # 下面会pop出来，为了更新单人的多订单
            "member_name": order.member_name,  # 下面会pop出来，只为了日志输出
            "phrase1": {
                "value": phrase1
            },
            "thing2": {
                "value": order.course_name
            },
            "time3": {
                "value": order.create_time.strftime("%y年%m月%d日 %H:%M")
            },
            "character_string4": {
                "value": order.order_no
            }
        })['order_ids'].append(order.id)

    if not user_notice_dict:
        return

    user_map: typing.Dict[str, UserModel] = await identifier_user_map()

    # 开始发送
    for member_id, data in user_notice_dict.items():
        member_name = data.pop('member_name')
        log_prefix = f'prepare notice {member_name}, with {data}'
        order_ids = data.pop('order_ids')

        member = user_map.get(member_id)
        if member.subscribe_counts <= 0:
            logger.warning(log_prefix + ', no surplus subscribe_counts.')
            continue

        try:
            res = subscribe_send(member.openid, CONST.ORDER_STATUS_TEMPLATE, data)
        except Exception as e:
            logger.error(log_prefix + f', subscribe send exec, {e.__class__.__name__}<{str(e)}>')
        else:
            if res:
                logger.info(log_prefix + f', success.')
                for order_id in order_ids:
                    await OrderModel.update_one({CONST.ID: order_id, CONST.NOTIFIED: CONST.TRUE_STATUS})
            else:
                logger.error(log_prefix + f', refuse')

            # 成功则subscribe_counts-1，被拒绝则将subscribe_counts置0
            member_data = {
                CONST.ID: member_id,
                CONST.SUBSCRIBE_COUNTS: max(member.subscribe_counts - 1, 0) if res else 0
            }
            await UserModel.update_one(member_data)


async def run_tasks():
    aps.add_job(expire_order, 'cron', hour='0', minute='1')
    aps.add_job(order_notice, 'cron', hour='9', minute='30')
