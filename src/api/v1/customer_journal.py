# -*- coding:utf-8 -*-
from sanic.views import HTTPMethodView

from infra.utils import resp_success, resp_failure
from common.const import CONST
from orm.customer_journal_orm import find_customer_journals, create_customer_journals


class CustomerJournals(HTTPMethodView):
    sub_url = '/journals'

    @staticmethod
    async def get(request):
        """
        查看客户备注
        :param request:
        :return:
        """
        count, rst = await find_customer_journals(request, request.ctx.user)
        return resp_success({CONST.COUNT: count, CONST.LIST: rst})

    @staticmethod
    async def post(request):
        """
        填写新的客户备注
        :param request:
        :return:
        """
        is_success = await create_customer_journals(request, request.ctx.user)
        return resp_success() if is_success else resp_failure(CONST.OPERATION_FAILURE_CODE, CONST.OPERATION_FAILURE_MSG)
