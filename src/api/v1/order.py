from datetime import datetime, timedelta

from sanic.views import HTTPMethodView

from api import check_staff
from common.const import CONST
from common.enum import StaffRoleEnum, OrderStatusEnum
from infra.date_utils import get_datetime_zero, get_date_time_by_str
from infra.utils import resp_failure, resp_success
from orm.model import CourseModel, OrderModel, UserModel
from orm.order_orm import find_orders
from service.validate_service import validate_order_create_data, validate_order_comment_create_data, \
    validate_order_update_data, validate_order_expense_get_args


class Order(HTTPMethodView):
    @staticmethod
    @check_staff(StaffRoleEnum.iter.value)  # 给教练权限，是为用教练账号给会员签到
    async def get(request):
        """
        查看所有订单
        :param request:
        :return:
        """
        rst, err_msg = validate_order_expense_get_args(request, OrderStatusEnum)
        if not rst:
            return resp_failure(400, err_msg)

        return resp_success(await find_orders(request))

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def post(request):
        """
        开通会员
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_order_create_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        member: UserModel = await UserModel.get_one(id=data[CONST.MEMBER_ID])
        if not member.phone or not member.nickname:
            return resp_failure(400, "该会员还未完善资料")
        if member.staff_roles:
            return resp_failure(400, "无法为员工开通课程")

        data[CONST.MEMBER_NAME] = member.name_zh or member.nickname
        data[CONST.MEMBER_PHONE] = member.phone
        # 根据课程ID，找到课程相关信息
        course: CourseModel = await CourseModel.get_one(id=data[CONST.COURSE_ID])
        data[CONST.BILL_TYPE] = course.bill_type
        data[CONST.COURSE_NAME] = course.name
        # 有效次数，默认跟有效次数相同 FIXME 此处一般不准，需要去订单管理页，修改真实的有效次数。
        data[CONST.LIMIT_COUNTS] = course.limit_counts
        # 剩余次数，默认跟有效次数相同
        data[CONST.SURPLUS_COUNTS] = course.limit_counts
        # 到期时间，默认今天+有效天数+1
        data[CONST.EXPIRE_TIME] = get_datetime_zero(datetime.now() + timedelta(days=course.limit_days + 1))

        order = await OrderModel.create(**data)
        return resp_success(id=order.id)

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def put(request):
        """
        退款/更新
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_order_update_data(data)  # 里面对原始data有做修改
        if not rst:
            return resp_failure(400, err_msg)

        order: OrderModel = await OrderModel.get_one(id=data[CONST.ID])

        course_id = data.get(CONST.COURSE_ID)
        if course_id and course_id != order.course_id:
            # 有课程ID，将更新订单的课程ID、课程名、计费类型 这三个。
            course: CourseModel = await CourseModel.get_one(id=course_id)
            data[CONST.BILL_TYPE] = course.bill_type
            data[CONST.COURSE_NAME] = course.name

        expire_time = data.get(CONST.EXPIRE_TIME)
        if expire_time and get_date_time_by_str(expire_time + ' 00:00:00') > datetime.now():
            data[CONST.EXPIRE_TIME] = get_date_time_by_str(expire_time + ' 00:00:00')
        else:
            # data.pop(CONST.EXPIRE_TIME, None)  # 不能将到期时间改到过去
            return resp_failure(400, "过期时间不能是过去")

        limit_counts = data.get(CONST.LIMIT_COUNTS) or order.limit_counts
        surplus_counts = data.get(CONST.SURPLUS_COUNTS) or order.surplus_counts
        if surplus_counts > limit_counts:
            return resp_failure(400, "剩余次数不能大于有效次数")

        await OrderModel.update_one(data)
        return resp_success()


class OrderComment(HTTPMethodView):
    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def post(request):
        """
        新增订单备注（也会加一条用户备注）
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_order_comment_create_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        order: OrderModel = await OrderModel.get_one(order_no=data.pop(CONST.ORDER_NO))
        member: UserModel = await UserModel.get_one(id=order.member_id)
        user: UserModel = request.ctx.user
        # if not any([_ in user.staff_roles for _ in [StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value]]):
        #     assert order.coach_id == user.id, f"OrderModel[{order.id}] no access for user[{user.id}]"

        now_dt_str = datetime.now().strftime('%m/%d')
        this_comment = data.pop(CONST.COMMENT)

        data[CONST.ID] = order.id
        data[CONST.COMMENTS] = order.comments or []
        data[CONST.COMMENTS].append(f"({now_dt_str}){user.nickname}: {this_comment}")
        await OrderModel.update_one(data)

        member_data = {CONST.ID: member.id, CONST.COMMENTS: member.comments}
        member_data.setdefault(CONST.COMMENTS, []).append(f"({now_dt_str}){user.nickname}#{order.id}: {this_comment}")
        await UserModel.update_one(member_data)
        return resp_success()
