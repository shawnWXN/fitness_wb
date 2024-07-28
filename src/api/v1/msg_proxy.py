from sanic.views import HTTPMethodView

from api import check_authorize
from infra.utils import resp_success
from service.wx_openapi import send_api


class MsgProxy(HTTPMethodView):

    @staticmethod
    @check_authorize()
    async def get(request):
        """
        查看所有user
        :param request:
        :return:
        """
        oid: str = request.args.get('openid')
        tid: str = request.args.get('template_id')

        send_api(oid, tid)

        return resp_success()
