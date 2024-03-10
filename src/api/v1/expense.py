from sanic.views import HTTPMethodView

from infra.utils import resp_failure, resp_success, str2base64
from loggers.logger import logger
from uuid import uuid4


class Expense(HTTPMethodView):
    @staticmethod
    async def post(request):
        """
        生成核销码
        :param request:
        :return:
        """
        data = request.json or dict()
        if not data.get('order_no'):
            return resp_failure(400, "miss order_no in body.")
        qrcode_base64 = str2base64(uuid4().hex)
        return resp_success(qrcode=qrcode_base64)

    @staticmethod
    async def put(request):
        """
        核销
        :param request:
        :return:
        """
        expense_no = request.args.get('expense_no')
        if not expense_no:
            return resp_failure(400, "miss `expense_no` in query string")
        logger.info(f"收到核销码，核销码: {expense_no}")
        return resp_success()
