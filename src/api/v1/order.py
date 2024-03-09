from sanic.views import HTTPMethodView

from api import check_staff, check_authorized
from common.const import CONST
from common.enum import StaffRoleEnum, BillTypeEnum
from infra.utils import resp_failure, resp_success
from orm.course_orm import find_courses
from orm.model import CourseModel, UserModel
from service.validate_service import validate_course_create_data, validate_course_update_data


class Order(HTTPMethodView):
    @staticmethod
    @check_authorized
    async def post(request):
        """
        开通/续费会员
        :param request:
        :return:
        """
        return resp_success(await find_courses(request))


class OrderComment(HTTPMethodView):
    @staticmethod
    async def post(request):
        """
        订单备注
        :param request:
        :return:
        """
        ...


async def prepare_upsert(data: dict) -> tuple[bool, str | dict]:
    ...
