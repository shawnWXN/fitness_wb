import importlib
import inspect
import pkgutil
import re

import pyfiglet
from sanic import Sanic
from sanic.handlers import ErrorHandler
from sanic.views import HTTPMethodView
from tortoise.contrib.sanic import register_tortoise

from common.const import CONST
from infra.utils import resp_failure, camel2snake
from loggers.logger import logger
from orm.model import UserModel
from scheduler.core import aps
from settings.setting import SETTING

app = Sanic(CONST.SYSTEM_APP_NAME)


class GlobalErrorHandler(ErrorHandler):
    def default(self, request, exc):
        """
        handles errors that have no error handlers assigned
        """
        logger.exception(f"GlobalErrorHandler: {str(exc)}")
        if isinstance(exc, AssertionError) and "not found" in exc.args[-1]:
            return resp_failure(404, "记录不存在")

        # You custom error handling logic...
        return super().default(request, exc)


@app.middleware("request")
async def before_request(request):
    try:
        if "multipart/form-data" in request.headers.get('content-type'):
            body = "`multipart/form-data`"
        else:
            body = request.body.decode()
    except Exception:  # noqa
        body = request.body

    headers = []
    for header, value in request.headers.items():
        headers.append(f"{header}={value}")

    log_msg = f"{request.method} {request.path}, headers:{';'.join(headers)}, args:{request.args}, body:{body}"
    if not request.route:
        logger.warning(log_msg)  # 404时，return后将直接到ErrorHandler
        return

    # 获取x-wx-openid
    openid = request.headers.get('x-wx-openid') or None
    if not openid:
        return resp_failure(400, 'miss `x-wx-openid` in header.')

    request.ctx.user, _ = await UserModel.get_or_create(openid=openid)
    logger.info(log_msg)


@app.listener("before_server_start")
async def before_server_start(app, loop):
    aps.run(loop)


@app.listener("before_server_stop")
async def before_server_stop(app, loop):
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
        "KEEP_ALIVE_TIMEOUT": 15,  # Nginx performance tuning guidelines uses keepalive = 15 seconds
        "FALLBACK_ERROR_FORMAT": "json",
        "REAL_IP_HEADER": "X-Real-IP",
        "PROXIES_COUNT": 1
    }
    app.config.update(options)
    app.error_handler = GlobalErrorHandler()
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
                    'pool_recycle': 3600  # 回收无用db连接，解决`Packet sequence number wrong - got X expected 1` BUG
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


run_web_service()
