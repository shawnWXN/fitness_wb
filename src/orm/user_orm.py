from functools import reduce

from faker import Faker
from tortoise.queryset import Q

from api import paging
from common.const import CONST
from common.enum import StaffRoleEnum, GenderEnum
from orm.model import UserModel

fake = Faker("zh_CN")


async def faker_users():
    count = fake.random_int(1, 15)
    for _ in range(count):

        prefix = fake.uuid4().split('-')[0]
        if _ % 3 == 0:
            await UserModel.create(openid=prefix, staff_roles=[StaffRoleEnum.ADMIN.value, StaffRoleEnum.COACH.value])
        elif _ % 2 == 0:
            await UserModel.create(openid=prefix, gender=GenderEnum.MALE.value)
        else:
            await UserModel.create(openid=prefix)


async def find_users(request) -> dict:
    """
    店主/管理员查看用户列表
    """
    search: str = request.args.get(CONST.SEARCH)
    staff_roles: str = request.args.get(CONST.STAFF_ROLES)

    user: UserModel = request.ctx.user
    max_role = max(user.staff_roles)
    default_roles = [role for role in StaffRoleEnum.iter.value if role < max_role]  # 当前用户允许筛选的角色列表
    default_roles.append('null')  # 加入null的会员
    filter_roles = set(default_roles) & set(staff_roles.split(','))  # 与前端的staff_roles取交集
    # TODO 用户管理写到这了
    if not user.staff_roles:
        ...
    elif any([_ in user.staff_roles for _ in [StaffRoleEnum.MASTER.value, StaffRoleEnum.ADMIN.value]]):
        ...
    else:
        # 教练只看
        ...

    if _id:
        ...
    else:
        query = UserModel.filter()
        if search:
            if search.isdigit():
                query = query.filter(Q(phone__icontains=search))
            else:
                query = query.filter(Q(nickname__icontains=search))
        if staff_roles:
            query = query.filter(
                reduce(lambda x, y: x | y, [Q(staff_roles__contains=[int(role)]) for role in staff_roles.split(',')]))
    return await paging(request, query)
