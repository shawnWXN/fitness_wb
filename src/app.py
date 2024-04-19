import importlib
import inspect
import pkgutil
import re

import pyfiglet
from sanic import Sanic
from sanic.handlers import ErrorHandler
from sanic.request import Request
from sanic.views import HTTPMethodView
from tortoise.contrib.sanic import register_tortoise

from common.const import CONST
from infra.utils import resp_failure, camel2snake, get_openid
from loggers.logger import logger
from orm.model import UserModel
from scheduler.core import aps
from scheduler.tasks import run_tasks
from settings.setting import SETTING

app = Sanic(CONST.SYSTEM_APP_NAME)


class _GlobalErrorHandler(ErrorHandler):
    def default(self, request, exc):
        """
        handles errors that have no error handlers assigned
        """
        logger.exception(f"GlobalErrorHandler: {exc.__class__.__name__}<{str(exc)}>")
        if isinstance(exc, AssertionError):
            if "not found" in exc.args[-1]:
                return resp_failure(404, "记录不存在")
            if "no access" in exc.args[-1]:
                return resp_failure(403, "您的权限不足以操作")
        # You custom error handling logic...
        # return super().default(request, exc)
        return resp_failure(500, "哦豁，服务器开小差了~")


@app.middleware("request")
async def _before_request(request: Request):
    try:
        if "multipart/form-data" in request.headers.get('content-type'):
            body = "`multipart/form-data`"
        else:
            body = request.json
    except Exception:  # noqa
        body = request.body

    log_msg = f"{request.method} {request.path}, args:{request.args}, body:{body}"
    if not request.route:
        logger.warning(log_msg + ", status_code 404.")
        return resp_failure(404, f"路径不存在")

    openid = get_openid(request)
    if not openid:
        logger.warning(log_msg + ", status_code 400.")
        return resp_failure(400, f"not found openid.")

    user = await UserModel.get_or_none(openid=openid)
    if not user:
        user = UserModel(id=-1, openid=openid)
    user_info = f", user[id={user.id},openid={user.openid},role={user.staff_roles}], args:"
    # if request.method.upper() != 'GET':
    logger.info(log_msg.replace(", args:", user_info))
    request.ctx.user = user


# 定义响应中间件
@app.middleware("response")
async def _custom_header(request: Request, response):
    response.headers["Sanic-App-Version"] = "04172346"


@app.listener("before_server_start")
async def _before_server_start(app, loop):
    aps.run(loop)
    await run_tasks()


@app.listener("before_server_stop")
async def _before_server_stop(app, loop):
    aps.stop()


def register_routes(module_name, prefix=""):
    module = importlib.import_module(module_name)
    for _, name, pkg in pkgutil.iter_modules(module.__path__):
        sub_name = module.__name__ + "." + name
        if pkg:
            register_routes(sub_name, module_name + "/" + name)
        else:
            for _, obj in inspect.getmembers(importlib.import_module(sub_name)):
                if inspect.isclass(obj) and issubclass(obj, HTTPMethodView) and obj != HTTPMethodView:
                    app.add_route(obj.as_view(), f'{CONST.URL_PREFIX}/{prefix}/{camel2snake(_)}')
                    logger.info(f"endpoint: {CONST.URL_PREFIX}/{prefix}/{camel2snake(_)}")


def run_web_service():
    logger.info("\n" + pyfiglet.Figlet(width=200).renderText(app.name))
    options = {
        "DEBUG": False,
        "ACCESS_LOG": False,
        "KEEP_ALIVE_TIMEOUT": 15,  # Nginx tuning guidelines uses keepalive = 15 seconds
        "FALLBACK_ERROR_FORMAT": "json",
        "REAL_IP_HEADER": "X-Real-IP",
        "PROXIES_COUNT": 1
    }
    app.config.update(options)
    app.error_handler = _GlobalErrorHandler()
    register_routes('api')

    pattern = r"(?P<dialect>\w+)://(?P<user>\w+):(?P<password>\w+)@(?P<host>[\d.]+):(?P<port>\d+)/(?P<db>\w+)"
    m = re.match(pattern, SETTING.MYSQL_URI)
    tortoise_config = {
        'connections': {
            'default': {
                'engine': 'tortoise.backends.mysql',
                'credentials': {
                    'host': m.group('host'),
                    'port': m.group('port'),
                    'user': m.group('user'),
                    'password': m.group('password'),
                    'database': m.group('db'),
                    'pool_recycle': 180  # 回收无用db连接，解决`Packet sequence number wrong - got X expected 1` BUG
                }
            }
        },
        'apps': {
            CONST.SYSTEM_NAME: {  # 随意拟定
                'models': ['orm.model'],  # 以根目录开始，模型定义所在的模块名
                'default_connection': 'default'  # 表明用connections.default里面的配置（适用配置多个数据源）
            }
        },
        'timezone': 'Asia/Shanghai'  # 默认是UTC
    }
    register_tortoise(app, config=tortoise_config, generate_schemas=True)
    logger.warning("SERVER IS DEV MODE.") if SETTING.DEV else logger.warning("SERVER IS PRODUCTION MODE.")


run_web_service()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
