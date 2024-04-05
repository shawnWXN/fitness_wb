from sanic.views import HTTPMethodView

from api import check_staff, check_authorize
from common.const import CONST
from common.enum import StaffRoleEnum, BillTypeEnum
from infra.utils import resp_failure, resp_success, days_bill_description
from orm.course_orm import find_courses
from orm.model import CourseModel
from service.validate_service import validate_course_create_data, validate_course_update_data


class Course(HTTPMethodView):
    @staticmethod
    async def get(request):
        """
        查看所有课程
        :param request:
        :return:
        """
        # TODO 有暴刷风险
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

        await prepare_data(data)

        # 判断教练ID真实性
        # user: UserModel = await UserModel.get_one(id=data[CONST.COACH_ID])
        # if StaffRoleEnum.COACH.value not in user.staff_roles or not user.nickname:
        #     return resp_failure(400, "教练不存在或未设置昵称")

        # data[CONST.COACH_NAME] = user.nickname
        course: CourseModel = await CourseModel.create(**data)
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

        await prepare_data(data)

        # course: CourseModel = await CourseModel.get_one(id=data[CONST.ID])
        # coach_id = data.get(CONST.COACH_ID)
        # # 有更新教练信息
        # if coach_id and course.coach_id != coach_id:
        #     # 判断教练ID真实性
        #     user: UserModel = await UserModel.get_one(id=coach_id)
        #     if StaffRoleEnum.COACH.value not in user.staff_roles or not user.nickname:
        #         return resp_failure(400, "教练不存在或未设置昵称")

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
    @check_authorize(exclude_staff=True)
    async def get(request):
        """
        咨询更多
        :param request:
        :return:
        """
        course_id = request.args.get(CONST.COURSE_ID) or 0
        # course: CourseModel = await CourseModel.get_one(id=course_id)
        # coach: UserModel = await UserModel.get_one(id=course.coach_id)
        # async with aiohttp.ClientSession() as session:
        #     await session.post(
        #         'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e020e7e0-cdd9-4f55-83cf-8f800db5b316',
        #         json={
        #             'msgtype': 'text',
        #             'text': {
        #                 "content": "hello world"
        #             }
        #         }
        #     )

        return resp_success(phone='19318578554')


async def prepare_data(data: dict):
    # 计次卡设置潜在超时（当前默认设置一年）
    # 计时卡设置潜在次数（当前默认每天三次）
    if data.get(CONST.BILL_TYPE) == BillTypeEnum.DAY.value:
        if not data.get(CONST.LIMIT_COUNTS):
            data[CONST.LIMIT_COUNTS] = data[CONST.LIMIT_DAYS] * 3
        data[CONST.BILL_DESC] = days_bill_description(data[CONST.LIMIT_DAYS])

    if data.get(CONST.BILL_TYPE) == BillTypeEnum.COUNT.value:
        if not data.get(CONST.LIMIT_DAYS):
            data[CONST.LIMIT_DAYS] = 365
        data[CONST.BILL_DESC] = f"{data[CONST.LIMIT_COUNTS]}课时"
