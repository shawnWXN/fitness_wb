from api import paging
from common.const import CONST
from orm.model import CourseModel


async def find_courses(request) -> dict:
    """
    课程列表
    """
    _id: str = request.args.get(CONST.ID)
    search: str = request.args.get(CONST.SEARCH)
    query = CourseModel.filter()
    if _id:
        query = query.filter(id=_id)
    elif search:
        query = query.filter(name__icontains=search)

    return await paging(request, query)

    # search: str = request.args.get(CONST.SEARCH)
    # query = CourseModel.filter()
    # if search:
    #     query = query.filter(Q(name__icontains=search) | Q(coach_name__icontains=search))

    # return await paging(request, query)


async def pk_thumbnail_map() -> dict:
    courses = await CourseModel.all()
    return {course.id: course.thumbnail for course in courses}
