# -*- coding:utf-8 -*-
from datetime import datetime

from faker import Faker
from tortoise.queryset import Q

from common.const import CONST
from infra.date_utils import minus_day_hour
from orm.customer_journal_orm import insert_one as insert_journal, del_by_cid as del_journal_by_cid, latest_allot_by_cid
from orm.model import Customer
from orm.user_orm import user_id_obj, find_by_id as find_user_by_id

fake = Faker("zh_CN")


# ------------------- service function -------------------
async def faker_customers():
    count = fake.random_int(1, 200)
    for _ in range(count):
        await Customer.create(cname=fake.company(), brand=fake.bs(), domain=fake.domain_name(),
                              contact_name=fake.name(), contact_position=fake.word(), qq=fake.aba(),
                              wechat=fake.word(), email=fake.email(), phone=fake.phone_number(),
                              schema=CONST.PUBLIC)


async def find_my_customers(request, user: dict) -> tuple:
    search = request.args.get(CONST.SEARCH)
    c_id = request.args.get(CONST.ID)
    page_size = request.args.get(CONST.PAGE_SIZE)
    page_num = request.args.get(CONST.PAGE_NUM)

    back_list = list()
    query = Customer.filter(is_active=CONST.TRUE_STATUS, schema=CONST.PRIVATE, u_id=user.get(CONST.ID))

    if c_id and c_id.isdigit():
        query = query.filter(id=int(c_id))

    if search:
        query = query.filter(Q(cname__icontains=search) | Q(brand__icontains=search)
                             | Q(domain__icontains=search) | Q(contact_name__icontains=search)
                             | Q(qq__icontains=search) | Q(wechat__icontains=search)
                             | Q(email__icontains=search) | Q(phone__icontains=search))

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
    objs = await query.order_by('-update_time').offset(offset).limit(page_size)

    for obj in objs:
        back_list.append(obj.to_dict())

    return count, back_list


async def find_customer_seas(request, user: dict) -> tuple:
    search = request.args.get(CONST.SEARCH)
    uid = request.args.get(CONST.U_ID)
    schema = request.args.get(CONST.SCHEMA)
    page_size = request.args.get(CONST.PAGE_SIZE)
    page_num = request.args.get(CONST.PAGE_NUM)

    back_list = list()
    query = Customer.filter(is_active=CONST.TRUE_STATUS)
    if search:
        query = query.filter(Q(cname__icontains=search) | Q(brand__icontains=search)
                             | Q(domain__icontains=search) | Q(contact_name__icontains=search)
                             | Q(qq__icontains=search) | Q(wechat__icontains=search)
                             | Q(email__icontains=search) | Q(phone__icontains=search))

    if uid and uid.isdigit():
        query = query.filter(u_id=int(uid))

    if schema in (CONST.PRIVATE, CONST.PUBLIC):
        query = query.filter(schema=schema)

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
    objs = await query.order_by('-update_time').offset(offset).limit(page_size)

    user_id_dict = await user_id_obj()
    for obj in objs:
        d = obj.to_dict()
        d[CONST.NICK_NAME] = user_id_dict.get(d.get(CONST.U_ID), {}).get(CONST.NICK_NAME)

        # 公海客户
        if d.get(CONST.SCHEMA, CONST.PUBLIC) == CONST.PUBLIC:
            # 没有分配时长
            d[CONST.ALLOT_GAP] = None
            # 全放开
            # if user.get(CONST.ROLE) == 10:
            #     d[CONST.CONTACT_NAME], d[CONST.CONTACT_POSITION], d[CONST.QQ], \
            #         d[CONST.WECHAT], d[CONST.EMAIL], d[CONST.PHONE] = ['*'] * 6
            #     # 因为只有返回null，前端才能让用户无法点开备注记录，故此
            #     d[CONST.JOURNAL] = None

        # 私有客户
        elif d.get(CONST.SCHEMA, CONST.PUBLIC) == CONST.PRIVATE:
            # 管理员查看
            if user.get(CONST.ROLE) == 1:
                # 计算一下分配时长
                latest_allot = await latest_allot_by_cid(d[CONST.ID], user)
                if latest_allot:
                    now = datetime.now()
                    d[CONST.ALLOT_GAP] = "{}d{}h".format(*minus_day_hour(latest_allot.get(CONST.CREATE_TIME, now), now))
                else:
                    logger.error(f"customer[id={d[CONST.ID]}, schema=private], but not found latest `allot` journal.")
                    d[CONST.ALLOT_GAP] = None
            # 普通销售查看
            else:
                # 自己的客户
                if user.get(CONST.ID) == d.get(CONST.U_ID):
                    # 计算一下分配时长
                    latest_allot = await latest_allot_by_cid(d[CONST.ID], user)
                    if latest_allot:
                        now = datetime.now()
                        d[CONST.ALLOT_GAP] = "{}d{}h".format(*minus_day_hour(latest_allot.get(CONST.CREATE_TIME), now))
                    else:
                        logger.error(
                            f"customer[id={d[CONST.ID]}, schema=private], but not found latest `allot` journal.")
                        d[CONST.ALLOT_GAP] = None
                # 不是自己的客户
                else:
                    # 隐藏以下8个信息
                    d[CONST.CONTACT_NAME], d[CONST.CONTACT_POSITION], d[CONST.QQ], \
                        d[CONST.WECHAT], d[CONST.EMAIL], d[CONST.PHONE], d[CONST.ALLOT_GAP] = ['*'] * 7
                    # 因为只有返回null，前端才能让用户无法点开备注记录，故此
                    d[CONST.JOURNAL] = None
        else:
            d[CONST.ALLOT_GAP] = None

        back_list.append(d)

    return count, back_list


async def update_customer_seas(data, user: dict) -> bool:
    op = data.get(CONST.OP)
    if op not in CONST.SEAS_OP_ENUM:
        logger.error(f"op={op} is invalid")
        return False

    c_id = int(data.get(CONST.ID, 0))
    obj = await Customer.filter(id=c_id, is_active=CONST.TRUE_STATUS).get_or_none()
    if not obj:
        logger.info(f"Customer[id={c_id}, is_active=T] not found")
        return False

    # 分配：只能管理员
    if op == CONST.ALLOT:
        if user.get(CONST.ROLE) != 1:
            logger.error(f"not permission when op={op} and role={user.get(CONST.ROLE)}")
            return False

        if not data.get(CONST.U_ID, 0):
            logger.error(f"miss u_id when op={op}")
            return False

        if obj.u_id == int(data.get(CONST.U_ID)):
            logger.warning(f"customer.u_id is {obj.u_id} already when op={op}")
            return True

        user_dict = await find_user_by_id(int(data.get(CONST.U_ID)))
        if not user_dict:
            return False

        update_data = {CONST.ID: c_id, CONST.SCHEMA: CONST.PRIVATE, CONST.U_ID: int(data.get(CONST.U_ID))}
        await update_one(update_data, user)

    # 退回：销售和管理员都行
    elif op == CONST.BACK:
        if obj.u_id is None:
            logger.error(f"old customer.u_id is none when op={op}")
            return False

        if not data.get(CONST.CONTENT):
            logger.error(f"need content when op={op}")
            return False

        if obj.u_id != user.get(CONST.ID):
            if user.get(CONST.ROLE) == 1:
                update_data = {CONST.ID: c_id, CONST.SCHEMA: CONST.PUBLIC, CONST.U_ID: None,
                               CONST.CONTENT: data.get(CONST.CONTENT)}
                await update_one(update_data, user)
            else:
                # 非管理员，不允许退回他人客户
                logger.error(
                    f"not permission when op={op} and customer[u_id={obj.u_id}] != user[id={user.get(CONST.ID)}]"
                    f" and role={user.get(CONST.ROLE)}")
                return False
        else:
            update_data = {CONST.ID: c_id, CONST.SCHEMA: CONST.PUBLIC, CONST.U_ID: None,
                           CONST.CONTENT: data.get(CONST.CONTENT)}
            await update_one(update_data, user)

    # 删除：只能管理员
    elif op == CONST.DEL:
        if user.get(CONST.ROLE) != 1:
            logger.error(f"not permission when op={op} and role={user.get(CONST.ROLE)}")
            return False

        if not data.get(CONST.CONTENT):
            logger.error(f"need content when op={op}")
            return False

        update_data = {CONST.ID: c_id, CONST.IS_ACTIVE: CONST.FALSE_STATUS,
                       CONST.CONTENT: data.get(CONST.CONTENT)}
        await update_one(update_data, user)
        await del_journal_by_cid(c_id, user)
    else:
        logger.error(f"op={op} is invalid")
        return False

    return True


# ------------------- dao function -------------------
async def find_by_id(c_id: int) -> dict:
    obj = await Customer.filter(id=c_id, is_active=CONST.TRUE_STATUS).get_or_none()
    return obj.to_dict() if obj else dict()


async def customer_ids_by_view_journal(u_id: int):
    """
        返回u_id对应的普通user有权看备注的客户id
    :param u_id: 这个user肯定是普通角色
    :return:
    """
    back_list = list()

    fields = [CONST.ID]
    objs = await Customer.filter((Q(u_id=u_id) | Q(u_id=None)), is_active=CONST.TRUE_STATUS).only(*fields).all()

    for obj in objs:
        back_list.append(obj.id)

    return back_list


async def customer_ids_by_user(u_id: int):
    back_list = list()

    fields = [CONST.ID]
    objs = await Customer.filter(u_id=u_id, is_active=CONST.TRUE_STATUS).only(*fields).all()

    for obj in objs:
        back_list.append(obj.id)

    return back_list


async def insert_one(data, user: dict):
    if user.get(CONST.ROLE) not in (1, 10):
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return

    if not any([data.get(CONST.CNAME), data.get(CONST.BRAND), data.get(CONST.DOMAIN),
                data.get(CONST.CONTACT_NAME), data.get(CONST.CONTACT_POSITION), data.get(CONST.QQ),
                data.get(CONST.WECHAT), data.get(CONST.PHONE), data.get(CONST.EMAIL)]):
        logger.error(f"add customer error, {data} param error")
        return False

    field_map = {CONST.CNAME: '公司名', CONST.BRAND: '品牌名', CONST.DOMAIN: '域名', CONST.CONTACT_NAME: '联系人',
                 CONST.CONTACT_POSITION: '联系人职位', CONST.QQ: 'QQ', CONST.WECHAT: '微信', CONST.PHONE: '手机',
                 CONST.EMAIL: '邮箱'}
    journal_data = dict()
    c = Customer()
    for k, v in data.items():
        c.__setattr__(k, v)
        if v and field_map.get(k):
            journal_data[field_map.get(k)] = v

    # c.__setattr__(CONST.SCHEMA, CONST.PRIVATE)
    # c.__setattr__(CONST.U_ID, user.get(CONST.ID))

    journal = f"系统事件：录入公司，信息：{journal_data}"
    c.__setattr__(CONST.JOURNAL, journal)
    await c.save()

    await insert_journal({CONST.C_ID: c.id, CONST.CONTENT: journal}, user)
    await update_one({CONST.ID: c.id, CONST.SCHEMA: CONST.PRIVATE, CONST.U_ID: user.get(CONST.ID)}, user)


async def update_one(data: dict, user: dict) -> bool:
    if user.get(CONST.ROLE) not in (1, 10):
        logger.error(f"role={user.get(CONST.ROLE)} is invalid")
        return False

    c_id = int(data.get(CONST.ID, 0))
    obj = await Customer.filter(id=c_id, is_active=CONST.TRUE_STATUS).get_or_none()
    if not obj:
        logger.info(f"Customer[id={c_id}, is_active=T] not found")
        return False

    if user.get(CONST.ROLE) != 1 and user.get(CONST.ID) != obj.u_id:
        logger.error(f"Customer[u_id={obj.u_id}] != user[id={user.get(CONST.ID)}]")
        return False

    # 统一放弃接收journal，data里面有content才增加journal
    data.get(CONST.JOURNAL) is not None and data.pop(CONST.JOURNAL)

    old_cname = obj.cname
    old_is_active = obj.is_active
    old_u_id = obj.u_id

    await obj.update_from_dict(data)

    if data.get(CONST.CONTENT, ""):
        await insert_journal({CONST.C_ID: c_id, CONST.CONTENT: data.get(CONST.CONTENT)}, user)
        obj.journal = data.get(CONST.CONTENT)

    if data.get(CONST.IS_ACTIVE) in (CONST.TRUE_STATUS, CONST.FALSE_STATUS):
        journal = f"系统事件：更改激活状态，原[{old_is_active}]->新[{data.get(CONST.IS_ACTIVE)}]"

        await insert_journal({CONST.C_ID: c_id, CONST.CONTENT: journal}, user)
        obj.journal = journal

    if data.get(CONST.CNAME, "") and data.get(CONST.CNAME, "") != old_cname:
        journal = f"系统事件：修改公司名，原[{old_cname}]->新[{data.get(CONST.CNAME)}]"

        await insert_journal({CONST.C_ID: c_id, CONST.CONTENT: journal}, user)
        obj.journal = journal

    if data.get(CONST.U_ID, 0):
        # 如果有传u_id，并且它不为0，说明是更换销售
        old_u = await find_user_by_id(old_u_id)
        new_u = await find_user_by_id(int(data.get(CONST.U_ID)))
        journal = f"系统事件：指派销售，原[{old_u.get(CONST.NICK_NAME)}]->新[{new_u.get(CONST.NICK_NAME)}]"

        await insert_journal({CONST.C_ID: c_id, CONST.CONTENT: journal}, user)
        obj.journal = journal

    if data.get(CONST.U_ID, 0) is None:
        # 如果传u_id = None，说明是退回
        old_u = await find_user_by_id(old_u_id, None)  # 在old_u_id已删除的情况下，此处需要传值is_active=None
        journal = f"系统事件：退回公海，原销售[{old_u.get(CONST.NICK_NAME)}]"

        await insert_journal({CONST.C_ID: c_id, CONST.CONTENT: journal}, user)
        obj.journal = journal

    await obj.save()
    return True
