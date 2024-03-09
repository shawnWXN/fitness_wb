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
                    logger.info(f"Request[{resp.url}], Response[{resp.status}] ->{resp.text}")
                    for key, value in resp.headers.items():
                        logger.info(f"{key}: {value}")
                    resp_json = await resp.json()
                    logger.info(f"resp_json: {resp_json}")
                    data = resp_json['data_list'][0]
                    phone_info = json.loads(data['json'])['data']
                    phone_number = phone_info['phoneNumber']
                    return resp_success({"phone": phone_number})
                except Exception as e:
                    logger.exception(e)
                    return resp_failure(500, f'get phone failed, {str(e)}')
