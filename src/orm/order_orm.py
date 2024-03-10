from datetime import datetime, timedelta
from tortoise.queryset import Q

from api import paging
from common.const import CONST
from orm.model import OrderModel


async def my_orders(request) -> dict:
    """
    我的订单列表
    """
    search: str = request.args.get(CONST.SEARCH)
    status: str = request.args.get(CONST.STATUS)
    create_date_start: datetime = request.ctx.args.get(CONST.CREATE_DATE_START)
    create_date_end: datetime = request.ctx.args.get(CONST.CREATE_DATE_END)

    query = OrderModel.filter(member_id=request.ctx.user.id)  # 首先过滤自己的订单

    if search:
        query = query.filter(Q(course_name__icontains=search) | Q(coach_name__icontains=search))

    # 根据状态过滤
    if status:
        query = query.filter(status=status)

    # 根据创建日期过滤
    date_format = "%Y-%m-%d"
    if create_date_start:
        query = query.filter(create_time__gte=create_date_start.strftime(date_format))
    if create_date_end:
        query = query.filter(create_time__lt=(create_date_end + timedelta(days=1)).strftime(date_format))  # 要加一天

    return await paging(request, query)