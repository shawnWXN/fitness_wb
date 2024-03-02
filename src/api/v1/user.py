# -*- coding:utf-8 -*-
import json

from sanic.views import HTTPMethodView
from aiohttp import ClientSession

from common.const import CONST
from infra.utils import resp_success, resp_failure
from orm.user_orm import find_users, create_user, modify_user


class Users(HTTPMethodView):
    sub_url = '/users'

    @staticmethod
    async def get(request):
        """
        查看所有user
        :param request:
        :return:
        """
        # await faker_users()
        count, rst = await find_users(request)
        return resp_success({CONST.COUNT: count, CONST.LIST: rst})

    @staticmethod
    async def post(request):
        """
        新增user，仅限管理员
        :param request:
        :return:
        """
        is_success, passwd_or_reason = await create_user(request, request.ctx.user)
        return resp_success({CONST.TOKEN: passwd_or_reason}) if is_success else resp_failure(
            CONST.OPERATION_FAILURE_CODE, passwd_or_reason)

    @staticmethod
    async def put(request):
        """
        编辑（删除）user信息
        :param request:
        :return:
        """
        is_success, reason = await modify_user(request, request.ctx.user)
        return resp_success() if is_success else resp_failure(CONST.OPERATION_FAILURE_CODE, reason)


class UserPhone(HTTPMethodView):
    @staticmethod
    async def post(request):

        x_wx_openid = request.headers.get('x-wx-openid')
        api = f"http://api.weixin.qq.com/wxa/getopendata?openid={x_wx_openid}"
        cloudid = request.json.get("cloudid")

        async with ClientSession() as session:
            async with session.post(api, json={"cloudid_list": [cloudid]},
                                    headers={'Content-Type': 'application/json'}) as resp:
                try:
                    resp_json = await resp.json()
                    data = resp_json['data_list'][0]
                    phone_info = json.loads(data['json'])['data']
                    phone_number = phone_info['phoneNumber']
                    return resp_success({"phone": phone_number})
                except Exception as e:
                    return resp_failure({"error": "get phone failed"}, status=500)
