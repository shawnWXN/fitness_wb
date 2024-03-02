# -*- coding:utf-8 -*-
from enum import IntEnum
from datetime import datetime

from tortoise.models import Model
from tortoise import fields

from common.const import CONST
from infra.date_utils import get_date_time_str


class BaseModel(Model):

    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    is_active = fields.CharField(100, default=CONST.TRUE_STATUS)
    create_time = fields.DatetimeField(auto_now_add=True)
    update_time = fields.DatetimeField(auto_now=True)

    def to_dict(self, *field):
        d = dict()
        for c in field or self._meta.fields:
            attr_name = c if isinstance(c, str) else c.name
            value = getattr(self, attr_name)
            if isinstance(value, datetime):
                value = get_date_time_str(value)
            d[attr_name] = value
        return d


class User(BaseModel):

    class Meta:
        table = "user"

    class RoleEnum(IntEnum):
        ADMIN = 1
        STAFF = 10

    nick_name = fields.CharField(100)
    user_name = fields.CharField(100)
    passwd = fields.CharField(100)
    role = fields.IntEnumField(RoleEnum)

    def to_dict(self, *field):
        d = dict()
        for c in field or self._meta.fields:
            attr_name = c if isinstance(c, str) else c.name
            value = getattr(self, attr_name)
            if isinstance(value, datetime):
                value = get_date_time_str(value)
            # 去掉密码响应
            if attr_name == CONST.PASSWD:
                continue

            d[attr_name] = value
        return d


class Customer(BaseModel):

    class Meta:
        table = "customer"

    cname = fields.CharField(100, null=True)
    brand = fields.CharField(100, null=True)
    domain = fields.CharField(100, null=True)
    contact_name = fields.CharField(100, null=True)
    contact_position = fields.CharField(100, null=True)
    qq = fields.CharField(100, null=True)
    wechat = fields.CharField(100, null=True)
    email = fields.CharField(100, null=True)
    phone = fields.CharField(100, null=True)
    journal = fields.CharField(4096, null=True)
    schema = fields.CharField(100, default=CONST.PUBLIC)
    u_id = fields.IntField(null=True)


class CustomerJournal(BaseModel):

    class Meta:
        table = "customer_journal"

    c_id = fields.IntField()
    u_id = fields.IntField()
    content = fields.CharField(4096)
