from sanic.views import HTTPMethodView

from api import check_staff, check_authorize
from common.const import CONST
from common.enum import StaffRoleEnum, OrderStatusEnum, ExpenseStatusEnum
from infra.utils import resp_success, resp_failure
from orm.expense_orm import my_expenses
from orm.model import UserModel
from orm.order_orm import my_orders
from orm.user_orm import find_users, update_user
from service.validate_service import validate_userprofile_update_data, validate_user_update_data, \
    validate_order_expense_get_args
from service.wx_openapi import phone_via_code


class User(HTTPMethodView):

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def get(request):
        """
        查看所有user
        :param request:
        :return:
        """
        staff_roles: str = request.args.get(CONST.STAFF_ROLES)

        allowed_roles: set = set(map(str, StaffRoleEnum.iter.value))
        allowed_roles.add('null')

        if staff_roles and set(staff_roles.split(',')) - allowed_roles:
            return resp_failure(400, f'`员工角色` 不在指定范围')

        return resp_success(await find_users(request))

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def put(request):
        """
        修改user的权限
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_user_update_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        await update_user(request)
        return resp_success()


class UserProfile(HTTPMethodView):
    @staticmethod
    async def get(request):
        """
        查看profile
        :param request:
        :return:
        """
        # logger.info(f"UserProfile return {request.ctx.user.to_dict()}")
        return resp_success(data=request.ctx.user.to_dict())

    @staticmethod
    async def put(request):
        """
        更新profile：手机，昵称，头像，性别
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_userprofile_update_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        data.update({CONST.ID: request.ctx.user.id})
        user = await UserModel.update_one(data)
        request.ctx.user = user
        return resp_success()


class UserPhone(HTTPMethodView):
    @staticmethod
    async def get(request):
        """
        code换手机号（注意服务端访问的开发接口，需要在云托管配置该接口免token访问）
        1. 小程序端使用专用组件：https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/getPhoneNumber.html
        2. 服务端：https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-info/phone-number/getPhoneNumber.html
        """
        code = request.args.get('code')
        if not code:
            return resp_failure(400, "缺少必要参数")

        return resp_success(phone=phone_via_code(code))


class UserOrder(HTTPMethodView):
    @staticmethod
    @check_authorize(exclude_staff=True)
    async def get(request):
        """
        我的订单（已开通课程即订单状态为“activated”）
        :param request:
        :return:
        """
        rst, err_msg = validate_order_expense_get_args(request, OrderStatusEnum)
        if not rst:
            return resp_failure(400, err_msg)

        return resp_success(await my_orders(request))


class UserExpense(HTTPMethodView):
    @staticmethod
    @check_authorize(exclude_staff=True)
    async def get(request):
        """
        我的上课记录
        :param request:
        :return:
        """
        rst, err_msg = validate_order_expense_get_args(request, ExpenseStatusEnum)
        if not rst:
            return resp_failure(400, err_msg)

        return resp_success(await my_expenses(request))
