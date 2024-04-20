from datetime import datetime

import pytz
from sanic.views import HTTPMethodView

from api import check_staff, check_authorize
from common.enum import StaffRoleEnum, ScanSceneEnum, OrderStatusEnum
from infra.utils import resp_failure, resp_success, str2base64
from orm.model import OrderModel, UserModel, ExpenseModel
from service.validate_service import validate_qrcode_create_data


# qrcode_storage = {}  # qrcode_str -> ts
# qrcode_expire_ts = 5 * 60


class Qrcode(HTTPMethodView):

    @staticmethod
    @check_authorize(exclude_staff=True)
    async def post(request):
        """
        会员调用。根据场景，生成二维码
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_qrcode_create_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        sc: str = data.get('scene')
        _id: str = data.get('uuid')

        qrcode_str = f'{sc}#{_id}'
        if sc == ScanSceneEnum.EXPENSE.value:
            order: OrderModel = await OrderModel.get_one(order_no=_id)
            member: UserModel = await UserModel.get_one(id=order.member_id)
            assert member.id == request.ctx.user.id, f"OrderModel[{order.order_no}] no access for user[{request.ctx.user.id}]"
        else:  # 签到
            member: UserModel = await UserModel.get_one(openid=_id)
            assert member.id == request.ctx.user.id, f"OrderModel[{_id}] no access for user[{request.ctx.user.id}]"

        # logger.info(f"start {qrcode_str} -> {time.time_ns()}")
        # qrcode_storage[qrcode_str] = time.time_ns()
        # logger.info(f"now qrcode_storage {qrcode_storage}")
        return resp_success(qrcode=str2base64(qrcode_str))

    @staticmethod
    @check_staff([StaffRoleEnum.COACH.value])
    async def put(request):
        """
        教练调用。处理扫码结果
        :param request:
        :return:
        """
        scene_uuid: str = (request.json or dict()).get('scene_uuid')
        if not scene_uuid:
            return resp_failure(400, "缺少必要参数")

        # 判断有无过期
        # logger.info(f"now qrcode_storage {qrcode_storage}")
        # ts: typing.Optional[float, None] = qrcode_storage.pop(scene_uuid, None)
        # logger.info(f"pop qrcode_storage get {ts}")
        # if not ts or (ts + qrcode_expire_ts * pow(10, 9)) < time.time_ns():
        #     return resp_failure(500, "二维码已失效")

        sc, _id = scene_uuid.split('#', maxsplit=1)
        if sc == ScanSceneEnum.EXPENSE.value:
            order: OrderModel = await OrderModel.get_one(order_no=_id)
            # 判断订单状态是否activated、还在有效期、剩余次数大于零
            if order.status != OrderStatusEnum.ACTIVATED or order.expire_time <= datetime.now(
                    pytz.timezone('Asia/Shanghai')) or order.surplus_counts <= 0:
                raise AssertionError(f"OrderModel[{order.order_no}] no access for activated")

            # 组装数据
            data = dict(
                member_id=order.member_id,
                member_name=order.member_name,
                member_phone=order.member_phone,
                coach_id=request.ctx.user.id,
                coach_name=request.ctx.user.nickname or request.ctx.user.name_zh,
                course_id=order.course_id,
                course_name=order.course_name,
                order_no=order.order_no,
            )
            expense: ExpenseModel = await ExpenseModel.create(**data)
            # 订单剩余次数减一
            order.surplus_counts -= 1  # TODO 需要设置一天最多扫3次
            await order.save()
            return resp_success(scene=sc, id=expense.id)
        else:  # 签到
            member: UserModel = await UserModel.get_one(openid=_id)
            return resp_success(scene=sc, data=member.to_dict())
