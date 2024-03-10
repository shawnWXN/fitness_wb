from sanic.views import HTTPMethodView

from infra.utils import resp_failure, resp_success
from loggers.logger import logger


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
        return resp_success(path=f"/fitness/wb/api/v1/expense?id={data.get('order_no')}")

    @staticmethod
    async def put(request):
        """
        核销
        :param request:
        :return:
        """
        order_id = request.args.get('id')
        if not order_id:
            return resp_failure(400, "miss `id` in query string")
        logger.info(f"收到核销码，订单ID: {order_id}")
        return resp_success()
