import random
import typing
from datetime import datetime, timedelta

from sanic.views import HTTPMethodView
from faker import Faker
from tortoise.expressions import RawSQL

from api import check_staff
from api.v1.course import prepare_data
from common.const import CONST
from common.enum import StaffRoleEnum, BillTypeEnum
from infra.date_utils import get_datetime_zero
from infra.utils import resp_success
from orm.model import CourseModel, UserModel, OrderModel

mock = Faker('zh_CN')


class MockSystem(HTTPMethodView):

    @staticmethod
    @check_staff([StaffRoleEnum.ADMIN.value])
    async def post(request):
        """
        mock
        :param request:
        :return:
        """
        # 课程
        for _ in range(15):
            data = {
                "name": mock.name() + '课程',
                "intro": mock.sentence() + mock.sentence(),
                "thumbnail": "http://dummyimage.com/120x60",
                "bill_type": random.choice(BillTypeEnum.iter.value),
                "description": mock.paragraph() + mock.paragraph(),
                "desc_images": [
                    "http://dummyimage.com/120x600",
                    "http://dummyimage.com/468x60",
                    "http://dummyimage.com/728x90"
                ],
                "limit_days": random.choice([30, 90, 180, 365]),
                "limit_counts": random.randint(1, 999)
            }

            await prepare_data(data)
            await CourseModel.create(**data)
        # 下单
        courses: typing.List[CourseModel] = await CourseModel.all()
        objs: typing.List[UserModel] = await UserModel.annotate(
            staff_roles_length=RawSQL("JSON_LENGTH(staff_roles)")).filter(staff_roles_length=0).all()
        for obj in objs:
            if not all([obj.nickname, obj.nickname]):
                continue
            for i in range(7):
                dd = {CONST.MEMBER_ID: obj.id, CONST.COURSE_ID: random.choice(courses).id, CONST.MEMBER_PHONE: obj.phone,
                      'amount': random.randint(1, 999), 'receipt': 'http://dummyimage.com/468x60',
                      'contract': 'http://dummyimage.com/728x90', CONST.MEMBER_NAME: obj.nickname}

                # 根据课程ID，找到课程相关信息
                course: CourseModel = await CourseModel.get_one(id=dd[CONST.COURSE_ID])
                dd[CONST.BILL_DESC] = course.bill_desc
                dd[CONST.COURSE_NAME] = course.name
                # 到期时间，默认今天+有效天数+1
                dd[CONST.EXPIRE_TIME] = get_datetime_zero(datetime.now() + timedelta(days=course.limit_days + 1))
                # 剩余次数，默认跟有效次数相同
                dd[CONST.SURPLUS_COUNTS] = course.limit_counts

                await OrderModel.create(**dd)

        # 核销
        return resp_success()
