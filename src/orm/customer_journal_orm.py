# -*- coding:utf-8 -*-
from tortoise.queryset import Q

from common.const import CONST
from loggers.logger import logger
from orm.model import CustomerJournal


# ------------------- service function -------------------
async def find_customer_journals(request, user: dict) -> tuple:
    # 避免循环引用
    from orm.customer_orm import customer_ids_by_view_journal
    from orm.customer_orm import find_by_id as find_customer_by_id
    from orm.user_orm import find_by_id as find_user_by_id

    search = request.args.get(CONST.SEARCH)
    c_id = request.args.get(CONST.C_ID)
    u_id = request.args.get(CONST.U_ID)
    page_size = request.args.get(CONST.PAGE_SIZE)
    page_num = request.args.get(CONST.PAGE_NUM)

    back_list = list()
    query = CustomerJournal.filter(is_active=CONST.TRUE_STATUS)
    if search:
        query = query.filter(Q(content__icontains=search))

    if c_id and c_id.isdigit():
        if user.get(CONST.ROLE) != 1:
            journal_customer_ids = await customer_ids_by_view_journal(user.get(CONST.ID))
            if int(c_id) not in journal_customer_ids:
                logger.warning(f"Customer[id={c_id}] not belong to user[id={user.get(CONST.ID)}]")
                return 0, list()
        query = query.filter(c_id=int(c_id))
    else:
        # 未指定cid时，非管理员只能看自己客户和公海客户的备注
        if user.get(CONST.ROLE) != 1:
            journal_customer_ids = await customer_ids_by_view_journal(user.get(CONST.ID))
            if not journal_customer_ids:
                logger.warning(f"No customers belong to user[id={user.get(CONST.ID)}]")
                return 0, list()
            query = query.filter(c_id__in=journal_customer_ids)

    if u_id and u_id.isdigit():
        if user.get(CONST.ROLE) != 1:
            if int(u_id) != user.get(CONST.ID):
                logger.warning(
                    f"user[id={user.get(CONST.ID)}, role={user.get(CONST.ROLE)}] forbid access journal written by user[id={u_id}]")
                return 0, list()
        query = query.filter(u_id=int(u_id))

    if page_size and page_size.isdigit():
        page_size = int(page_size)
        page_size = page_size if page_size <= 50 else 50
    else:
        page_size = 10
    if page_num and page_num.isdigit():
        page_num = int(page_num) or 1
    else:
        page_num = 1
    offset = page_size * (page_num - 1)

    count = await query.count()
    objs = await query.order_by('-id').offset(offset).limit(page_size)

    for obj in objs:
        d = obj.to_dict()
        c_dict = await find_customer_by_id(d.get(CONST.C_ID, 0))
        u_dict = await find_user_by_id(d.get(CONST.U_ID, 0))
        d[CONST.CNAME] = c_dict.get(CONST.CNAME)
        d[CONST.NICK_NAME] = u_dict.get(CONST.NICK_NAME)
        back_list.append(d)

    return count, back_list


async def create_customer_journals(request, user: dict) -> bool:
    from orm.customer_orm import find_by_id as find_customer_by_id
    from orm.customer_orm import update_one as update_one_customer
    from orm.user_orm import find_by_id as find_user_by_id

    c_dict = await find_customer_by_id(int(request.json.get(CONST.C_ID)))
    u_dict = await find_user_by_id(user.get(CONST.ID))
    if not c_dict or not u_dict:
        return False

    if not request.json.get(CONST.CONTENT):
        logger.error("content is none")
        return False

    journal_data = {CONST.ID: int(request.json.get(CONST.C_ID)), CONST.CONTENT: request.json.get(CONST.CONTENT)}
    await update_one_customer(journal_data, user)
    return True


# ------------------- dao function -------------------
async def insert_one(data, user: dict):
    if user.get(CONST.ROLE) not in (1, 10):
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return

    if not all([data.get(CONST.C_ID), data.get(CONST.CONTENT)]):
        return

    data.update({CONST.U_ID: user.get(CONST.ID)})

    await CustomerJournal.create(**data)


async def del_by_cid(c_id: int, user: dict):
    if user.get(CONST.ROLE) not in (1, 10):
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return

    await CustomerJournal.filter(c_id=c_id, is_active=CONST.TRUE_STATUS).update(is_active=CONST.FALSE_STATUS)


async def latest_allot_by_cid(c_id: int, user: dict):
    if user.get(CONST.ROLE) not in (1, 10):
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return

    obj = await CustomerJournal \
        .filter(c_id=c_id, content__startswith='系统事件：指派销售', is_active=CONST.TRUE_STATUS) \
        .order_by('-id').first()

    return obj.to_dict() if obj else dict()
