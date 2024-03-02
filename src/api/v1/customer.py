# -*- coding:utf-8 -*-
from sanic.views import HTTPMethodView

from common.const import CONST
from infra.utils import resp_success, resp_failure
from loggers.logger import logger
from orm.customer_orm import find_customer_seas, update_customer_seas
from orm.customer_orm import insert_one, update_one, find_my_customers


class Customers(HTTPMethodView):
    sub_url = '/customers'

    @staticmethod
    async def get(request):
        """
        查看我的客户
        :param request:
        :return:
        """
        # await faker_customers()
        count, rst = await find_my_customers(request, request.ctx.user)
        return resp_success({CONST.COUNT: count, CONST.LIST: rst})

    @staticmethod
    async def post(request):
        """
        录入新的客户信息
        :param request:
        :return:
        """
        await insert_one(request.json, request.ctx.user)
        return resp_success()

    @staticmethod
    async def put(request):
        """
        修改客户信息（如果有cname, content字段，customer表和customer_journal表都会更新）
        :param request:
        :return:
        """
        data = request.json or dict()
        data.update({CONST.ID: request.args.get(CONST.ID, 0)})
        is_success = await update_one(data, request.ctx.user)
        return resp_success() if is_success else resp_failure(CONST.OPERATION_FAILURE_CODE, CONST.OPERATION_FAILURE_MSG)


class CustomerSeas(HTTPMethodView):
    sub_url = '/customer_seas'

    @staticmethod
    async def get(request):
        """
        查看公海客户
        按多项搜索，是否分配，销售id
        :param request:
        :return:
        """
        count, rst = await find_customer_seas(request, request.ctx.user)
        return resp_success({CONST.COUNT: count, CONST.LIST: rst})

    @staticmethod
    async def put(request):
        """
        修改公海客户信息（分配，退回，删除）
        :param request:
        :return:
        """
        data = request.json or dict()
        data.update({CONST.ID: request.args.get(CONST.ID, 0)})
        is_success = await update_customer_seas(data, request.ctx.user)
        return resp_success() if is_success else resp_failure(CONST.OPERATION_FAILURE_CODE, CONST.OPERATION_FAILURE_MSG)


class BatchCustomers(HTTPMethodView):
    sub_url = '/batch_customers'

    @staticmethod
    async def put(request):
        """
        批量修改公海客户信息（分配，退回，删除）
        :param request:
        :return:
        """

        c_ids = list()
        ori_c_ids = request.args.get(CONST.ID, '').split(',')

        for c_id_str in ori_c_ids:
            if c_id_str == '':
                continue
            try:
                c_ids.append(int(c_id_str))
            except Exception as e:
                logger.exception(f'int({c_id_str}) meet error: {str(e)}')

        if not c_ids:
            resp_failure(CONST.OPERATION_FAILURE_CODE, CONST.OPERATION_FAILURE_MSG)

        c_ids = set(c_ids)
        logger.info(f"batch_customers recv valid c_ids: {c_ids}")

        data = request.json or dict()
        for c_id in c_ids:
            data.update({CONST.ID: c_id})
            await update_customer_seas(data, request.ctx.user)
        return resp_success()
