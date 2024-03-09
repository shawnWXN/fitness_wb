from faker import Faker
from tortoise.queryset import Q

from api import paging
from common.const import CONST
from orm.model import CourseModel

fake = Faker("zh_CN")


# ------------------- service function -------------------
async def find_courses(request) -> dict:
    """
    课程列表
    """
    _id: str = request.args.get(CONST.ID)
    search: str = request.args.get(CONST.SEARCH)
    query = CourseModel.filter()
    if _id:
        query = query.filter(id=_id)
    else:
        if search:
            query = query.filter(Q(name__icontains=search) | Q(coach_name__icontains=search))

    return await paging(request, query)
