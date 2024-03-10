from sanic.views import HTTPMethodView

from api import check_authorize, check_staff
from common.const import CONST
from common.enum import StaffRoleEnum
from infra.date_utils import get_today_date_time
from infra.utils import resp_failure, resp_success
from loggers.logger import logger
from orm.model import CourseModel, OrderModel, UserModel
from service.validate_service import validate_order_create_data, validate_order_comment_create_data, \
    validate_order_update_data


class Order(HTTPMethodView):
    @staticmethod
    @check_authorize(exclude_staff=True)
    async def post(request):
        """
        开通/续费会员
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_order_create_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        data[CONST.MEMBER_ID] = request.ctx.user.id
        data[CONST.MEMBER_NAME] = request.ctx.user.nickname
        # 根据课程ID，找到课程相关信息
        course: CourseModel = await CourseModel.get_one(_id=data[CONST.COURSE_ID])  # 可能404（直接删除、教练解聘级联删除）
        # 补全教练信息、课程信息、计费类型、有效天数和次数
        data[CONST.COURSE_NAME] = course.name
        data[CONST.COACH_ID] = course.coach_id
        data[CONST.COACH_NAME] = course.coach_name
        data[CONST.BILL_TYPE] = course.bill_type
        data[CONST.LIMIT_DAYS] = course.limit_days
        data[CONST.LIMIT_COUNTS] = course.limit_counts
        data[CONST.SURPLUS_COUNTS] = course.limit_counts  # 剩余天数，默认跟有效天数相同

        order = await OrderModel.create(**data)
        return resp_success(id=order.id)

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def put(request):
        """
        更新订单(非pending的order，更新按钮叫“更新并激活”)
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_order_update_data(data)  # 里面对原始data有做修改
        if not rst:
            return resp_failure(400, err_msg)

        order: OrderModel = await OrderModel.get_one(_id=data[CONST.ID])
        course_id = data.get(CONST.COURSE_ID)
        if course_id and course_id != order.course_id:
            # 根据课程ID，找到课程相关信息
            course: CourseModel = await CourseModel.get_one(_id=course_id)  # 可能404（直接删除、教练解聘级联删除）
            data[CONST.COURSE_NAME] = course.name
            data[CONST.COACH_ID] = course.coach_id
            data[CONST.COACH_NAME] = course.coach_name
        limit_counts = data.get(CONST.LIMIT_COUNTS)
        if limit_counts and limit_counts != order.limit_counts:
            gap = limit_counts - order.limit_counts
            order.surplus_counts += gap
            if order.surplus_counts < 0:
                return resp_failure(400, "有效课时超过了已消费课时")
            data[CONST.SURPLUS_COUNTS] = order.surplus_counts

        logger.info(f"data: {data}")
        await OrderModel.update_one(data)
        return resp_success()


class OrderComment(HTTPMethodView):
    @staticmethod
    @check_staff(StaffRoleEnum.iter.value)
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

        order: OrderModel = await OrderModel.get_one(_id=data.pop(CONST.ORDER_ID))
        member: UserModel = await UserModel.get_one(_id=order.member_id)
        user: UserModel = request.ctx.user
        if not any([_ in user.staff_roles for _ in [StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value]]):
            assert order.coach_id == user.id, f"OrderModel[{order.id}] no access for user[{user.id}]"

        now_dt_str = get_today_date_time()
        this_comment = data.pop(CONST.COMMENT)

        data[CONST.ID] = order.id
        data[CONST.COMMENTS] = order.comments or []
        data[CONST.COMMENTS].append(f"({now_dt_str}) User({user.id},{user.nickname}): {this_comment}")
        await order.update_one(data)

        member_data = {CONST.ID: member.id, CONST.COMMENTS: member.comments}
        member_data.setdefault(CONST.COMMENTS, []).append(
            f"({now_dt_str}) User({user.id},{user.nickname}) Order({order.id}): {this_comment}")
        await member.update_one(member_data)
        return resp_success()
