# -*- coding:utf-8 -*-
from functools import reduce

from faker import Faker
from tortoise.queryset import Q

from api import paging
from common.const import CONST
from common.enum import StaffRoleEnum, GenderEnum
from loggers.logger import logger
from orm.model import User

fake = Faker("zh_CN")


# ------------------- service function -------------------
async def demo_asp(arg):
    un = fake.name()
    obj = await User.filter(user_name=un, is_active=CONST.TRUE_STATUS).get_or_none()
    logger.info(f'arg: {arg}, find: {un}, result: {obj.to_dict() if obj else dict()}')
    # logger.info("demo")


async def faker_users():
    count = fake.random_int(1, 15)
    for _ in range(count):

        prefix = fake.uuid4().split('-')[0]
        if _ % 3 == 0:
            await User.create(openid=prefix, staff_roles=[StaffRoleEnum.ADMIN.value, StaffRoleEnum.COACH.value])
        elif _ % 2 == 0:
            await User.create(openid=prefix, gender=GenderEnum.MALE.value)
        else:
            await User.create(openid=prefix)


async def create_user(request, user: dict):
    if user.get(CONST.ROLE) != 1:
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return False, "权限不足"

    if not all([request.json.get(CONST.NICK_NAME), request.json.get(CONST.USER_NAME),
                int(request.json.get(CONST.ROLE, 0)) in (1, 10)]):
        logger.error(f"{request.json} param error")
        return False, "参数错误"

    exist_user = await find_by_un(request.json.get(CONST.USER_NAME))
    if exist_user:
        logger.error(f"user_name={request.json.get(CONST.USER_NAME)} already existed")
        return False, "登录名已存在"

    clear_passwd = fake.password()
    crypt_passwd = 'encrypt(clear_passwd)'

    data = request.json or dict()
    data[CONST.ROLE] = int(data[CONST.ROLE])
    data.update({CONST.PASSWD: crypt_passwd})

    is_success = await insert_one(data, user)
    if not is_success:
        return False, "操作失败"

    return True, clear_passwd


async def modify_user(request, user: dict):
    if user.get(CONST.ROLE) not in (1, 10):
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return False, '权限错误'

    data = request.json or dict()
    data[CONST.ID] = int(request.args.get(CONST.ID, 0))

    u_dict = await find_by_id(data.get(CONST.ID))
    if not u_dict:
        return False, f"未找到指定ID为{data.get(CONST.ID)}的用户"

    if data.get(CONST.USER_NAME) and data.get(CONST.USER_NAME) != u_dict.get(CONST.USER_NAME):
        exist_user = await find_by_un(data.get(CONST.USER_NAME))
        if exist_user:
            logger.error(f"user_name={data.get(CONST.USER_NAME)} already existed")
            return False, "登录名已存在"

    if user.get(CONST.ROLE) == 10:
        if user.get(CONST.ID) != data.get(CONST.ID):
            logger.error(f"not permission when user[id={user.get(CONST.ID)}, role={user.get(CONST.ROLE)}] "
                         f"to modify other user.id={data.get(CONST.ID)} ")
            return False, "无法修改他人信息"

        if not any([data.get(CONST.NICK_NAME), data.get(CONST.USER_NAME), data.get(CONST.PASSWD)]):
            return False, "至少修改一项"

        if data.get(CONST.PASSWD):
            data[CONST.PASSWD] = ...
        else:
            data.get(CONST.PASSWD) is not None and data.pop(CONST.PASSWD)

        # 保险起见，把role和is_active字段排除
        data.get(CONST.ROLE) is not None and data.pop(CONST.ROLE)
        data.get(CONST.IS_ACTIVE) is not None and data.pop(CONST.IS_ACTIVE)

        is_success, reason = await update_one(data, user)
        return is_success, reason

    else:
        if not any([data.get(CONST.NICK_NAME), data.get(CONST.USER_NAME), data.get(CONST.PASSWD),
                    data.get(CONST.ROLE), data.get(CONST.IS_ACTIVE)]):
            return False, "至少修改一项"

        if data.get(CONST.ROLE) and data.get(CONST.ROLE) not in (1, 10):
            return False, "权限错误"

        del_user = False
        if data.get(CONST.IS_ACTIVE):
            if data.get(CONST.IS_ACTIVE) not in (CONST.TRUE_STATUS, CONST.FALSE_STATUS):
                return False, "未知用户状态"

            if data.get(CONST.IS_ACTIVE) == CONST.FALSE_STATUS:
                if data.get(CONST.ID) == user.get(CONST.ID):
                    return False, "你不能删除自己"
                else:
                    del_user = True

        if data.get(CONST.PASSWD):
            data[CONST.PASSWD] = ...
        else:
            data.get(CONST.PASSWD) is not None and data.pop(CONST.PASSWD)

        is_success, reason = await update_one(data, user)
        # 如果是删除角色，那就把他名下的客户都退回公海
        if is_success and del_user:
            from orm.customer_orm import customer_ids_by_user
            from orm.customer_orm import update_one as update_customer_one
            u_customer_ids = await customer_ids_by_user(data.get(CONST.ID))
            for c_id in u_customer_ids:
                await update_customer_one({CONST.ID: c_id, CONST.SCHEMA: CONST.PUBLIC, CONST.U_ID: None}, user)

        return is_success, reason


async def find_users(request) -> dict:
    """
    users列表
    """

    search: str = request.args.get(CONST.SEARCH)
    staff_roles: str = request.args.get(CONST.STAFF_ROLES)
    # u_id = request.args.get(CONST.ID)
    # page_size = request.args.get(CONST.PAGE_SIZE)
    # page_num = request.args.get(CONST.PAGE_NUM)
    query = User.filter()
    if search:
        if search.isdigit():
            query = query.filter(Q(phone__icontains=search))
        else:
            query = query.filter(Q(nickname__icontains=search))
    if staff_roles:
        query = query.filter(reduce(lambda x, y: x | y, [Q(staff_roles__contains=[int(role)]) for role in staff_roles.split(',')]))
        # query = query.filter(Q(staff_roles__contains=[10]) | Q(staff_roles__contains=[20]))
    return await paging(request, query)

    # if u_id and u_id.isdigit():
    #     query = query.filter(id=int(u_id))
    #

    #
    # if page_size and page_size.isdigit():
    #     page_size = int(page_size)
    #     page_size = page_size if page_size <= 50 else 50
    # else:
    #     page_size = 10
    # if page_num and page_num.isdigit():
    #     page_num = int(page_num) or 1
    # else:
    #     page_num = 1
    # offset = page_size * (page_num - 1)



async def valid_id_un_role(user_id: int, un: str, role: int) -> dict:
    obj = await User.filter(id=user_id, is_active=CONST.TRUE_STATUS).get_or_none()
    if not obj:
        logger.info(f"User[id={user_id}, is_active=T] not found")
        return dict()

    if un != obj.user_name:
        logger.info(f"User[id={obj.id}, nick_name={obj.nick_name}, user_name={obj.user_name}] != {un}")
        return dict()

    if role != obj.role:
        logger.info(f"User[id={obj.id}, nick_name={obj.nick_name}, role={obj.role}] != {role}")
        return dict()

    return obj.to_dict()


# ------------------- dao function -------------------
async def user_id_obj():
    back_dict = dict()

    objs = await User.all()
    for obj in objs:
        back_dict.setdefault(obj.id, obj.to_dict())

    return back_dict


async def insert_one(data: dict, user: dict) -> bool:
    if user.get(CONST.ROLE) != 1:
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return False

    if not all([data.get(CONST.NICK_NAME), data.get(CONST.USER_NAME), data.get(CONST.PASSWD),
                data.get(CONST.ROLE) in (1, 10)]):
        logger.error(f"add user error, {data} param error")
        return False

    await User.create(**data)
    return True


async def update_one(data: dict, user: dict) -> tuple:
    if user.get(CONST.ROLE) not in (1, 10):
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return False, '权限错误'

    u_id = int(data.get(CONST.ID, 0))

    obj = await User.filter(id=u_id, is_active=CONST.TRUE_STATUS).get_or_none()
    if not obj:
        logger.info(f"User[id={u_id}, is_active=T] not found")
        return False, '未找到指定用户'

    for k, v in data.items():
        obj.__setattr__(k, v)

    await obj.save()
    return True, None


async def find_by_id(user_id: int, is_active=CONST.TRUE_STATUS) -> dict:
    if is_active in (CONST.TRUE_STATUS, CONST.FALSE_STATUS):
        obj = await User.filter(id=user_id, is_active=is_active).get_or_none()
    else:
        obj = await User.filter(id=user_id).get_or_none()
    return obj.to_dict() if obj else dict()


async def find_by_un(un: str) -> dict:
    obj = await User.filter(user_name=un, is_active=CONST.TRUE_STATUS).get_or_none()
    return obj.to_dict() if obj else dict()
