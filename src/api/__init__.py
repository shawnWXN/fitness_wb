from functools import wraps

from sanic.request import Request
from tortoise.queryset import QuerySet

from common.const import CONST
from infra.utils import resp_failure


async def paging(request: Request, query: QuerySet) -> dict:
    page_size = request.args.get(CONST.PAGE_SIZE)
    page_num = request.args.get(CONST.PAGE_NUM)
    if page_size and page_size.isdigit():
        page_size = int(page_size)
        page_size = page_size if page_size <= 100 else 100
    else:
        page_size = 50

    if page_num and page_num.isdigit():
        page_num = int(page_num) or 1
    else:
        page_num = 1

    count = await query.count()
    objs = await query.order_by('create_time').offset(page_size * (page_num - 1)).limit(page_size)
    items = [obj.to_dict() for obj in objs]
    return {
        'total': count,
        'page': page_num if count else 0,
        'size': len(items),
        'pages': (1 if count else 0) if count <= page_size else (
            count // page_size if count % page_size else count // page_size + 1),
        'items': items
    }


def check_staff(allowed_roles):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # 假设request.ctx.user是一个用户对象，包含phone属性
            user_phone = getattr(request.ctx.user, 'phone')
            # 检查用户是否有手机号
            if user_phone:
                # 假设request.ctx.user是一个用户对象，包含staff_roles属性
                user_roles = getattr(request.ctx.user, 'staff_roles', [])
                # 检查用户是否有允许的角色
                if any(role in allowed_roles for role in user_roles):
                    # 如果用户有权限，继续执行视图函数
                    return await f(request, *args, **kwargs)
                else:
                    # 如果用户没有权限，返回403禁止访问
                    return resp_failure(403, "Forbidden")
            else:
                # 返回401未经授权
                return resp_failure(401, "Unauthorized")

        return decorated_function

    return decorator


# def check_authorized_member(f):
#     async def decorated_function(request, *args, **kwargs):
#         # 假设request.ctx.user是一个用户对象，包含phone属性
#         user_phone = getattr(request.ctx.user, 'phone')
#         # 检查用户是否有手机号
#         if user_phone:
#             # 继续执行视图函数
#             return await f(request, *args, **kwargs)
#         else:
#             # 返回401未经授权
#             return resp_failure(401, "Unauthorized")
#
#     return decorated_function


def check_member(exclude_staff: bool = False):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # 假设request.ctx.user是一个用户对象，包含phone属性
            user_phone = getattr(request.ctx.user, 'phone')
            # 检查用户是否有手机号
            if user_phone:
                if not exclude_staff:
                    return await f(request, *args, **kwargs)
                else:
                    user_roles = getattr(request.ctx.user, 'staff_roles', [])
                    if not user_roles:
                        return await f(request, *args, **kwargs)
                    else:
                        return resp_failure(403, "Forbidden")
            else:
                # 返回401未经授权
                return resp_failure(401, "Unauthorized")

        return decorated_function

    return decorator
