from datetime import datetime

import pytz
from sanic.views import HTTPMethodView

from api import check_staff, check_authorize
from common.const import CONST
from common.enum import StaffRoleEnum, OrderStatusEnum, ExpenseStatusEnum
from infra.utils import resp_failure, resp_success, str2base64
from orm.expense_orm import find_expenses
from orm.model import OrderModel, UserModel, ExpenseModel
from service.validate_service import validate_expense_update_data, validate_order_expense_get_args


class Expense(HTTPMethodView):
    @staticmethod
    @check_staff(StaffRoleEnum.iter.value)
    async def get(request):
        """
        查看所有核销记录
        :param request:
        :return:
        """
        rst, err_msg = validate_order_expense_get_args(request, ExpenseStatusEnum)
        if not rst:
            return resp_failure(400, err_msg)

        return resp_success(await find_expenses(request))

    # @staticmethod
    # @check_staff([StaffRoleEnum.COACH.value])
    # async def post(request):
    #     """
    #     教练核销
    #     :param request:
    #     :return:
    #     """
    #     order_no = (request.json or dict()).get(CONST.ORDER_NO)
    #     if not order_no:
    #         return resp_failure(400, "缺少必要参数")
    #
    #     order: OrderModel = await OrderModel.get_one(order_no=order_no)
    #     # 判断订单状态是否activated、还在有效期、剩余次数大于零
    #     if order.status != OrderStatusEnum.ACTIVATED or order.expire_time <= datetime.now(
    #             pytz.timezone('Asia/Shanghai')) or order.surplus_counts <= 0:
    #         raise AssertionError(f"OrderModel[{order.order_no}] no access for activated")
    #
    #     # 组装数据
    #     data = dict(
    #         member_id=order.member_id,
    #         member_name=order.member_name,
    #         member_phone=order.member_phone,
    #         coach_id=request.ctx.user.id,
    #         coach_name=request.ctx.user.nickname or request.ctx.user.name_zh,
    #         course_id=order.course_id,
    #         course_name=order.course_name,
    #         order_no=order.order_no,
    #     )
    #     expense: ExpenseModel = await ExpenseModel.create(**data)
    #     # 订单剩余次数减一
    #     order.surplus_counts -= 1  # TODO 需要设置一天最多扫3次
    #     await order.save()
    #     return resp_success(id=expense.id)

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def put(request):
        """
        店主/管理员审核核销
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_expense_update_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        target_status: str = data.get(CONST.STATUS)
        expense: ExpenseModel = await ExpenseModel.get_one(id=data.get(CONST.ID))
        order: OrderModel = await OrderModel.get_one(order_no=expense.order_no)

        if target_status in [ExpenseStatusEnum.FREE.value, ExpenseStatusEnum.REJECT.value]:
            if expense.status in [ExpenseStatusEnum.PENDING, ExpenseStatusEnum.ACTIVATED]:  # 返还课时
                order.surplus_counts += 1

        if target_status == ExpenseStatusEnum.ACTIVATED.value:
            if expense.status in [ExpenseStatusEnum.REJECT, ExpenseStatusEnum.FREE]:  # 扣除课时
                order.surplus_counts -= 1

        expense.status = target_status
        await expense.save()
        await order.save()

        return resp_success()


# class ExpenseQrcode(HTTPMethodView):
#     @staticmethod
#     @check_authorize(exclude_staff=True)
#     async def get(request):
#         """
#         获取核销码（其实就是简单根据order_no生成二维码base64）
#         :param request:
#         :return:
#         """
#         order_no = request.args.get(CONST.ORDER_NO)
#         if not order_no:
#             return resp_failure(400, "缺少必要参数")
#
#         order: OrderModel = await OrderModel.get_one(order_no=order_no)
#         member: UserModel = await UserModel.get_one(id=order.member_id)
#         assert member.id == request.ctx.user.id, f"OrderModel[{order.order_no}] no access for user[{request.ctx.user.id}]"
#         return resp_success(qrcode=str2base64(order_no))
