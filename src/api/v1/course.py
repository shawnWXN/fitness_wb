from sanic.views import HTTPMethodView

from api import check_staff, check_member
from common.const import CONST
from common.enum import StaffRoleEnum, BillTypeEnum
from infra.utils import resp_failure, resp_success
from orm.course_orm import find_courses
from orm.model import CourseModel, UserModel
from service.validate_service import validate_course_create_data, validate_course_update_data


class Course(HTTPMethodView):
    @staticmethod
    async def get(request):
        """
        查看所有课程
        :param request:
        :return:
        """
        return resp_success(await find_courses(request))

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def post(request):
        """
        录入新的课程信息
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_course_create_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        rst, data = await prepare_upsert(data)
        if not rst:
            return resp_failure(400, data)

        course = await CourseModel.create(**data)
        return resp_success(id=course.id)

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def put(request):
        """
        修改课程
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_course_update_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        rst, data = await prepare_upsert(data)
        if not rst:
            return resp_failure(400, data)

        await CourseModel.update_one(data)
        return resp_success()

    @staticmethod
    @check_staff([StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value])
    async def delete(request):
        """
        删除课程
        :param request:
        :return:
        """
        await CourseModel.delete_one(request.args.get(CONST.ID) or 0)
        return resp_success()


class CourseConsult(HTTPMethodView):
    @staticmethod
    @check_member(exclude_staff=True)
    async def get(request):
        """
        咨询更多
        :param request:
        :return:
        """
        course_id = request.args.get(CONST.COURSE_ID) or 0
        course = await CourseModel.get_one(_id=course_id)
        # TODO 发送请求
        return resp_success()


async def prepare_upsert(data: dict) -> tuple[bool, str | dict]:
    # 计次卡设置潜在超时（当前默认设置一年）
    # 计时卡设置潜在次数（当前默认每天三次）
    if data.get(CONST.BILL_TYPE) == BillTypeEnum.DAY.value:
        data[CONST.LIMIT_COUNTS] = data[CONST.LIMIT_DAYS] * 3

    if data.get(CONST.BILL_TYPE) == BillTypeEnum.COUNT.value:
        data[CONST.LIMIT_DAYS] = 365

    # 判断教练ID真实性
    user = await UserModel.get_one(_id=data[CONST.COACH_ID])
    if StaffRoleEnum.COACH.value not in user.staff_roles or not user.nickname:
        return False, "教练不存在或未设置昵称"
    data[CONST.COACH_NAME] = user.nickname
    return True, data
