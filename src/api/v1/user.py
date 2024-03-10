from datetime import datetime
from sanic.views import HTTPMethodView

from api import check_staff, check_authorize
from common.const import CONST
from common.enum import StaffRoleEnum, OrderStatusEnum
from infra.utils import resp_success, resp_failure
from loggers.logger import logger
from orm.model import UserModel
from orm.order_orm import my_orders
from orm.user_orm import find_users

from service.validate_service import validate_userprofile_update_data


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
        if staff_roles and set(staff_roles.split(',')) - set(StaffRoleEnum.iter.value):
            return resp_failure(400, f'`staff_roles` 含有非法参数')

        pagination = await find_users(request)
        return resp_success(pagination)

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def put(request):
        """
        查看所有user
        :param request:
        :return:
        """
        # TODO 取消教练，对应课程也删除 + 提醒管理员或店主去修改在期订单的归属教练
        # await faker_users()
        pagination = await find_users(request)
        return resp_success(pagination)


class UserProfile(HTTPMethodView):
    @staticmethod
    async def get(request):
        """
        查看profile
        :param request:
        :return:
        """
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


class UserOrder(HTTPMethodView):
    @staticmethod
    @check_authorize(exclude_staff=True)
    async def get(request):
        """
        我的订单（课程即订单状态为“activated”）
        :param request:
        :return:
        """
        status: str = request.args.get(CONST.STATUS)
        create_date_start: str = request.args.get(CONST.CREATE_DATE_START)
        create_date_end: str = request.args.get(CONST.CREATE_DATE_END)

        # 要求1: 校验status
        if status and status not in OrderStatusEnum.iter.value:
            return resp_failure(400, f"`status` 不在指定范围")

        # 要求2: 校验日期格式
        request.ctx.args = dict()
        date_format = "%Y-%m-%d"
        try:
            if create_date_start:
                # 尝试将字符串转换为日期对象
                start_date = datetime.strptime(create_date_start, date_format)
                request.ctx.args[CONST.CREATE_DATE_START] = start_date  # 这里改str为datetime.datetime
            if create_date_end:
                # 尝试将字符串转换为日期对象
                end_date = datetime.strptime(create_date_end, date_format)
                request.ctx.args[CONST.CREATE_DATE_END] = end_date  # 这里改str为datetime.datetime
        except ValueError:
            # 如果转换失败，说明日期格式不正确
            return resp_failure(400, f"`create_date_start` or `create_date_end` 正则匹配失败")

        # 要求3: 校验create_date_end是否大于等于create_date_start
        if create_date_start and create_date_end:
            if end_date < start_date:  # noqa
                return resp_failure(400, f"`create_date_end`不得小于`create_date_start`")
        logger.info(f'request {request.args}')
        return resp_success(await my_orders(request))
