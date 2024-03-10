import typing
from datetime import datetime
from uuid import uuid4
from tortoise.models import Model
from tortoise import fields
from enum import Enum

from common.const import CONST
from common.enum import GenderEnum, BillTypeEnum, OrderStatusEnum
from infra.date_utils import get_date_time_str


class BaseModel(Model):
    T = typing.TypeVar('T', bound='BaseModel')

    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    create_time = fields.DatetimeField(auto_now_add=True)
    update_time = fields.DatetimeField(auto_now=True)

    @classmethod
    async def get_one(cls, _id: int) -> T:
        obj = await cls.get_or_none(id=_id)
        assert obj, f"{cls.__name__}[{_id}] not found"
        return obj

    @classmethod
    async def update_one(cls, data: dict) -> T:
        _id = data.pop(CONST.ID)
        assert _id, "miss model pk"
        obj = await cls.get_one(_id)

        for k, v in data.items():
            if v is not None:
                obj.__setattr__(k, v)
                await obj.save()
        return obj

    @classmethod
    async def delete_one(cls, _id: int):
        obj = await cls.get_one(_id)
        await obj.delete()

    def to_dict(self, *field) -> dict:
        d = dict()
        for c in field or self._meta.fields:
            attr_name = c if isinstance(c, str) else c.name
            value = getattr(self, attr_name)
            if isinstance(value, datetime):
                value = get_date_time_str(value)
            if isinstance(value, Enum):
                value = value.value
            d[attr_name] = value
        return d


class UserModel(BaseModel):
    class Meta:
        table = "user"

    openid = fields.CharField(max_length=255, unique=True, description="小程序openid")
    phone = fields.CharField(max_length=20, null=True, description="手机号")
    nickname = fields.CharField(max_length=50, null=True, description="微信昵称")
    gender = fields.CharEnumField(enum_type=GenderEnum, description="性别", max_length=1, null=True)
    avatar = fields.CharField(max_length=255, null=True, description="头像")
    staff_roles = fields.JSONField(description="账号权限列表", default=[])
    comments = fields.JSONField(description="备注", default=[])


class CourseModel(BaseModel):
    class Meta:
        table = "course"
        unique_together = [("name", "coach_id")]

    name = fields.CharField(max_length=255, description="课程名")
    intro = fields.TextField(description="课程简介")
    coach_id = fields.IntField(description="教练编号ID")
    coach_name = fields.CharField(max_length=255, description="教练名")
    thumbnail = fields.CharField(max_length=255, description="课程封面图")
    description = fields.TextField(null=True, description="课程详细文字")
    desc_images = fields.JSONField(description="课程详细图片", default=[])  # JSON field to store list of images
    bill_type = fields.CharEnumField(BillTypeEnum, description="计费类型")
    limit_days = fields.IntField(description="有效天数")
    limit_counts = fields.IntField(description="有效次数")


class OrderModel(BaseModel):
    class Meta:
        table = "order"

    member_id = fields.IntField(description="会员编号ID")
    member_name = fields.CharField(max_length=255, description="会员名")
    coach_id = fields.IntField(description="教练编号ID")
    coach_name = fields.CharField(max_length=255, description="教练名")
    course_id = fields.IntField(description="课程编号ID")
    course_name = fields.CharField(max_length=255, description="课程名")
    bill_type = fields.CharEnumField(BillTypeEnum, description="计费类型")
    limit_days = fields.IntField(description="有效天数")
    limit_counts = fields.IntField(description="有效次数")
    amount = fields.IntField(description="订单金额")
    receipt = fields.CharField(max_length=255, description="付款截图")
    contract = fields.CharField(null=True, max_length=255, description="合同文件")
    surplus_counts = fields.IntField(description="剩余次数")
    status = fields.CharEnumField(OrderStatusEnum, description="订单状态", default=OrderStatusEnum.PENDING.value)
    order_no = fields.CharField(unique=True, max_length=255, description="订单编号", default=lambda: uuid4().hex)
    comments = fields.JSONField(description="备注", default=[])
