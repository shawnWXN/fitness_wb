from functools import reduce

from tortoise.expressions import RawSQL
from tortoise.queryset import Q

from api import paging
from common.const import CONST
from common.enum import StaffRoleEnum
from orm.model import UserModel


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
    current_user_role = max(current_user.staff_roles) if current_user.staff_roles else 0

    data = request.json or dict()
    user: UserModel = await UserModel.get_one(id=data[CONST.ID])
    user_role = max(user.staff_roles) if user.staff_roles else 0

    assert user_role < current_user_role, f"UserModel[{user.id}] no access for user[{current_user.id}]"

    staff_roles = data.get(CONST.STAFF_ROLES)
    if staff_roles is not None:
        imparted_role = max(staff_roles) if staff_roles else 0
        assert imparted_role < current_user_role, f"no access to grant higher role via user[{current_user.id}]"
        await UserModel.update_one(data)
