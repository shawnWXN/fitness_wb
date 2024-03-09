import json

from sanic.views import HTTPMethodView
from aiohttp import ClientSession

from common.const import CONST
from infra.utils import resp_success, resp_failure
from orm.model import UserModel
from orm.user_orm import find_users
from loggers.logger import logger

from service.validate_service import validate_userprofile_update_data


class User(HTTPMethodView):

    @staticmethod
    async def get(request):
        """
        查看所有user
        :param request:
        :return:
        """
        # TODO 取消教练，对应课程也删除 + 提醒管理员或店主去修改在期订单的归属教练
        # await faker_users()
        pagination = await find_users(request)
        return resp_success(pagination)


class UserProfile(HTTPMethodView):
    @staticmethod
    async def get(request):
        """
        查看profile
        :param request:
        :return:
        """
        return resp_success(data=request.ctx.user.to_dict())

    @staticmethod
    async def put(request):
        """
        更新profile：手机，昵称，头像，性别
        :param request:
        :return:
        """
        data = request.json or dict()
        rst, err_msg = validate_userprofile_update_data(data)
        if not rst:
            return resp_failure(400, err_msg)

        data.update({CONST.ID: request.ctx.user.id})
        user = await UserModel.update_one(data)
        request.ctx.user = user
        return resp_success()
