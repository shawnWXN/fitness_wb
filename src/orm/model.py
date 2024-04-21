import shortuuid
import typing
from datetime import datetime
from tortoise.models import Model
from tortoise.queryset import QuerySet
from tortoise.functions import Count
from tortoise import fields
from enum import Enum

from common.const import CONST
from common.enum import BillTypeEnum, OrderStatusEnum, ExpenseStatusEnum
from infra.date_utils import get_date_time_str, get_date_str


class BaseModel(Model):
    T = typing.TypeVar('T', bound='BaseModel')

    class Meta:
        abstract = True

    id = fields.IntField(pk=True)
    create_time = fields.DatetimeField(auto_now_add=True)
    update_time = fields.DatetimeField(auto_now=True)

    @classmethod
    async def get_one(cls, **kwargs) -> T:
        obj = await cls.get_or_none(**kwargs)
        assert obj, f"{cls.__name__}[{kwargs.popitem()}] not found"
        return obj

    @classmethod
    async def update_one(cls, data: dict) -> T:
        _id = data.pop(CONST.ID)
        assert _id, "miss model pk"
        obj = await cls.get_one(id=_id)

        for k, v in data.items():
            if v is not None:
                obj.__setattr__(k, v)
                await obj.save()
        return obj

    @classmethod
    async def delete_one(cls, _id: int):
        obj = await cls.get_one(id=_id)
        await obj.delete()

    @classmethod
    async def count_via_group_by(cls, query: QuerySet, group_by: str, count_field: str = 'id') -> dict[typing.Any, int]:
        # 使用Tortoise ORM的聚合函数Count来分组并计数每个bill_type
        bill_type_counts = await query.annotate(count=Count(count_field)).group_by(group_by).values(group_by, 'count')
        return {entry[group_by]: entry['count'] for entry in bill_type_counts}

    def to_dict(self, *field) -> dict:
        d = dict()
        for c in field or self._meta.fields:
            attr_name = c if isinstance(c, str) else c.name
            value = getattr(self, attr_name)
            if isinstance(value, datetime):
                if attr_name == 'expire_time':
                    value = get_date_str(value)
                else:
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
    name_zh = fields.CharField(max_length=50, null=True, description="中文姓名")
    # gender = fields.CharEnumField(enum_type=GenderEnum, description="性别", max_length=1, null=True)
    avatar = fields.CharField(max_length=255, null=True, description="头像")
    staff_roles = fields.JSONField(description="账号权限列表", default=[])
    comments = fields.JSONField(description="备注", default=[])


class CourseModel(BaseModel):
    class Meta:
        table = "course"
        # unique_together = [("name", "coach_id")]

    name = fields.CharField(unique=True, max_length=255, description="课程名")
    intro = fields.TextField(description="课程简介")
    # coach_id = fields.IntField(description="教练编号ID")
    # coach_name = fields.CharField(max_length=255, description="教练名")
    thumbnail = fields.CharField(max_length=255, description="课程封面图")
    description = fields.TextField(null=True, description="课程详细文字")
    desc_images = fields.JSONField(description="课程详细图片", default=[])  # JSON field to store list of images
    bill_desc = fields.CharField(max_length=255, description="计费描述")
    bill_type = fields.CharEnumField(BillTypeEnum, description="计费类型")
    limit_days = fields.IntField(description="有效天数")
    limit_counts = fields.IntField(description="有效次数")


class OrderModel(BaseModel):
    class Meta:
        table = "order"

    member_id = fields.IntField(description="会员编号ID")
    member_name = fields.CharField(max_length=255, description="会员名")
    member_phone = fields.CharField(max_length=20, description="会员手机号")
    # coach_id = fields.IntField(description="教练编号ID")
    # coach_name = fields.CharField(max_length=255, description="教练名")
    course_id = fields.IntField(description="课程编号ID")
    course_name = fields.CharField(max_length=255, description="课程名")
    bill_type = fields.CharEnumField(BillTypeEnum, description="计费类型")
    # limit_days = fields.IntField(description="有效天数")
    # limit_counts = fields.IntField(description="有效次数")
    surplus_counts = fields.IntField(description="剩余次数")
    expire_time = fields.DatetimeField(description="到期时间")
    amount = fields.IntField(description="订单金额")
    receipt = fields.CharField(max_length=255, description="付款截图")
    contract = fields.CharField(null=True, max_length=255, description="合同文件")
    status = fields.CharEnumField(OrderStatusEnum, description="订单状态", default=OrderStatusEnum.ACTIVATED.value)
    order_no = fields.CharField(unique=True, max_length=255, description="订单编号", default=lambda: shortuuid.uuid())
    comments = fields.JSONField(description="备注", default=[])


class ExpenseModel(BaseModel):
    class Meta:
        table = "expense"

    member_id = fields.IntField(description="会员编号ID")
    member_name = fields.CharField(max_length=255, description="会员名")
    member_phone = fields.CharField(max_length=20, description="会员手机号")
    coach_id = fields.IntField(description="教练编号ID")
    coach_name = fields.CharField(max_length=255, description="教练名")
    course_id = fields.IntField(description="课程编号ID")
    course_name = fields.CharField(max_length=255, description="课程名")
    status = fields.CharEnumField(ExpenseStatusEnum, description="消费记录状态",
                                  default=ExpenseStatusEnum.PENDING.value)
    order_no = fields.CharField(max_length=255, description="订单编号")
    # comments = fields.JSONField(description="备注", default=[])
