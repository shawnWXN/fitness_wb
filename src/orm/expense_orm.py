import re
import typing
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from tortoise.expressions import Q

from api import paging
from common.const import CONST
from common.enum import StaffRoleEnum
from infra.utils import page_num_size
from orm.model import ExpenseModel, UserModel
from orm.order_orm import order_amount_avg


async def my_expenses(request) -> dict:
    """
    我的消费记录列表
    """
    order_no: str = request.args.get(CONST.ORDER_NO)
    search: str = request.args.get(CONST.SEARCH)
    status: str = request.args.get(CONST.STATUS)
    create_date_start: datetime = request.ctx.args.get(CONST.START_DT)
    create_date_end: datetime = request.ctx.args.get(CONST.END_DT)

    query = ExpenseModel.filter(member_id=request.ctx.user.id)  # 首先过滤自己的

    if order_no:
        query = query.filter(order_no=order_no)

    if search:
        query = query.filter(Q(course_name__icontains=search) | Q(coach_name__icontains=search))

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
    create_date_start: datetime = request.ctx.args.get(CONST.START_DT)
    create_date_end: datetime = request.ctx.args.get(CONST.END_DT)

    user: UserModel = request.ctx.user
    role = max(user.staff_roles) if user.staff_roles else 0

    query = ExpenseModel.filter()
    if StaffRoleEnum.COACH.value == role:
        query = query.filter(coach_id=user.id)
    if search:
        # 如果是order_no
        if re.match(r'^[a-zA-Z0-9]{22}$', search):
            query = query.filter(order_no=search)
        elif search.isdigit():
            query = query.filter(member_phone__icontains=search)
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

    pagination = await paging(request, query)
    page_num, _ = page_num_size(request)
    if page_num == 1:
        order_cnt_dict = await ExpenseModel.count_via_group_by(query, 'order_no')
        order_avg_dict: typing.Dict[str, Decimal] = await order_amount_avg()
        order_total_amount = sum([order_avg_dict.get(k) * Decimal(v) for k, v in order_cnt_dict.items()])
        order_total_amount = float(order_total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)) if order_total_amount else 0
        pagination['expense_amount'] = order_total_amount
    return pagination
