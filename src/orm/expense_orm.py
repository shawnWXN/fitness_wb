import re
from datetime import datetime, timedelta

from tortoise.expressions import Q

from api import paging
from common.const import CONST
from common.enum import StaffRoleEnum
from orm.model import ExpenseModel, UserModel


async def my_expenses(request) -> dict:
    """
    我的消费记录列表
    """
    order_no: str = request.args.get(CONST.ORDER_NO)
    status: str = request.args.get(CONST.STATUS)
    create_date_start: datetime = request.ctx.args.get(CONST.CREATE_DATE_START)
    create_date_end: datetime = request.ctx.args.get(CONST.CREATE_DATE_END)

    query = ExpenseModel.filter(member_id=request.ctx.user.id)  # 首先过滤自己的

    if order_no:
        query = query.filter(order_no=order_no)

    # 根据状态过滤
    if status:
        query = query.filter(status__in=status.split(','))

    # 根据创建日期过滤
    date_format = "%Y-%m-%d"
    if create_date_start:
        query = query.filter(create_time__gte=create_date_start.strftime(date_format))
    if create_date_end:
        query = query.filter(create_time__lt=(create_date_end + timedelta(days=1)).strftime(date_format))  # 要加一天

    return await paging(request, query)


async def find_expenses(request) -> dict:
    """
    消费记录列表
    """
    search: str = request.args.get(CONST.SEARCH)
    status: str = request.args.get(CONST.STATUS)
    create_date_start: datetime = request.ctx.args.get(CONST.CREATE_DATE_START)
    create_date_end: datetime = request.ctx.args.get(CONST.CREATE_DATE_END)

    user: UserModel = request.ctx.user
    role = max(user.staff_roles) if user.staff_roles else 0

    query = ExpenseModel.filter()
    if StaffRoleEnum.COACH.value == role:
        query = query.filter(coach_id=user.id)
    if search:
        # 如果是order_no
        if re.match(r'^[0-9a-f]{32}$', search):
            query = query.filter(order_no=search)
        else:
            query = query.filter(
                Q(member_name__icontains=search) | Q(coach_name__icontains=search) | Q(course_name__icontains=search))

    if status:
        query = query.filter(status__in=status.split(','))

    # 根据创建日期过滤
    date_format = "%Y-%m-%d"
    if create_date_start:
        query = query.filter(create_time__gte=create_date_start.strftime(date_format))
    if create_date_end:
        query = query.filter(create_time__lt=(create_date_end + timedelta(days=1)).strftime(date_format))  # 要加一天

    return await paging(request, query, ('expire_time', 'surplus_counts'))
