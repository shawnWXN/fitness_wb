from functools import reduce

from faker import Faker
from tortoise.expressions import RawSQL
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
    forbid_roles = [role for role in StaffRoleEnum.iter.value if role >= max_role]  # 当前用户禁止访问的角色列表

    query = UserModel.annotate(staff_roles_length=RawSQL("JSON_LENGTH(staff_roles)")).filter()
    if search:
        if search.isdigit():
            query = query.filter(Q(phone__icontains=search))
        else:
            query = query.filter(Q(nickname__icontains=search))

    filter_roles = set()
    if staff_roles:
        filter_roles: set = set(staff_roles.split(',')) - set(forbid_roles)  # 前端staff_roles减去forbid_roles

    if forbid_roles:
        query = query.filter(
            reduce(lambda x, y: x & y, [~Q(staff_roles__contains=[int(role)]) for role in forbid_roles]))

    if filter_roles:
        query = query.filter(
            reduce(lambda x, y: x | y,
                   [Q(staff_roles_length=0) if role == 'null' else Q(staff_roles__contains=[int(role)]) for role in
                    filter_roles]))

    return await paging(request, query)


async def update_user(request):
    current_user: UserModel = request.ctx.user
    current_user_role = max(current_user.staff_roles)

    data = request.json or dict()
    user: UserModel = await UserModel.get_one(_id=data[CONST.ID])
    user_role = max(user.staff_roles)

    assert user_role >= current_user_role, f"UserModel[{user.id}] no access for user[{current_user.id}]"

    staff_roles = data.get(CONST.STAFF_ROLES)
    if staff_roles is None:
        await user.update_one(data)
