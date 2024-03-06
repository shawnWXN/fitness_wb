# -*- coding:utf-8 -*-
from datetime import datetime

from tortoise.models import Model
from tortoise import fields

from common.const import CONST
from infra.date_utils import get_date_time_str


class BaseModel(Model):

    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    # is_active = fields.CharField(100, default=CONST.TRUE_STATUS)
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

    openid = fields.CharField(max_length=255, unique=True, description="小程序openid")
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    nickname = fields.CharField(max_length=50, null=True, description="微信昵称")
    gender = fields.CharField(max_length=1, null=True, description="性别", choices=[
        ("0", "未知"),
        ("1", "男性"),
        ("2", "女性"),
    ])
    avatar = fields.CharField(max_length=255, null=True, description="头像")
    staff_roles = fields.JSONField(description="账号权限列表", default=[])
    comments = fields.JSONField(description="备注", default=[])


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
