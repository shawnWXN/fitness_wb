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
from orm.user_orm import valid_id_un_role
from scheduler.core import aps
from settings.setting import SETTING

app = Sanic(CONST.SYSTEM_APP_NAME)


class GlobalErrorHandler(ErrorHandler):
    def default(self, request, exception):
        ''' handles errors that have no error handlers assigned '''
        logger.exception(f"global error handler: {str(exception)}")
        # You custom error handling logic...
        return super().default(request, exception)


# @app.middleware("request")
async def before_request(request):
    if CONST.URL_PREFIX not in request.path:
        return

    # 心跳接口或未知接口，都跳出请求拦截器
    if request.path.endswith("alive") or request.path.endswith("metrics") or request.path.endswith(
            "captcha") or not request.route:
        return

    try:
        if "multipart/form-data" in request.headers.get('content-type'):
            body = "`multipart/form-data`"
        else:
            body = request.body.decode()
    except Exception:
        body = request.body
    log_msg = f"{request.method} {request.path}, ip: {request.remote_addr}, args: {request.args}, body: {body}"

    # 登录接口不校验session_id
    if request.path.endswith("login"):
        logger.info(log_msg)
        return

    # 先查缓存
    k = f"{CONST.SYSTEM_SESSIONS_PREFIX}:{request.cookies.get(CONST.SESSION_ID, '')}"
    is_success, user = await get_from_redis(k, True)
    if not is_success:
        logger.warning(f"not found session from redis key={k}")
        return resp_failure(CONST.AUTH_INVALID_CODE, CONST.AUTH_INVALID_MSG, print_log=False)

    # 再查db
    user_id, user_name, user_role = user.get(CONST.ID), user.get(CONST.USER_NAME), user.get(CONST.ROLE)

    user = await valid_id_un_role(user_id, user_name, user_role)
    if not user:
        logger.warning(f"not found user[id={user_id}, user_name={user_name}] from db")
        return resp_failure(CONST.AUTH_INVALID_CODE, CONST.AUTH_INVALID_MSG, print_log=False)

    # PUT 和 POST都要带请求体
    if request.method.upper() in ('POST', 'PUT') and not request.body:
        logger.warning(f"request.body is none when request.method = {request.method}")
        return resp_failure(CONST.BODY_NONE_CODE, CONST.BODY_NONE_MSG, print_log=False)

    log_msg += f", user: {user}, session: {request.cookies.get(CONST.SESSION_ID, '')}"
    logger.info(log_msg)

    request.ctx.user = user


@app.middleware("response")
async def jsonify(request, response):
    if CONST.URL_PREFIX not in request.path:
        return


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
    # init_route(app)
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
