from functools import wraps

from sanic.request import Request
from tortoise.queryset import QuerySet

from infra.utils import resp_failure, page_num_size


async def paging(request: Request, query: QuerySet, order_by: tuple = ('-id',)) -> dict:
    page_num, page_size = page_num_size(request)

    count = await query.count()
    objs = await query.order_by(*order_by).offset(page_size * (page_num - 1)).limit(page_size)
    items = [obj.to_dict() for obj in objs]
    return {
        'total': count,
        'page': page_num if count else 0,
        'size': len(items),
        'pages': (1 if count else 0) if count <= page_size else (
            count // page_size + 1 if count % page_size else count // page_size),
        'items': items
    }


def check_staff(allowed_roles: list):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # 假设request.ctx.user是一个用户对象，包含phone属性
            user_phone = getattr(request.ctx.user, 'phone')
            nickname = getattr(request.ctx.user, 'nickname')
            # 检查用户是否有手机号
            if user_phone and nickname:
                # 假设request.ctx.user是一个用户对象，包含staff_roles属性
                user_roles = getattr(request.ctx.user, 'staff_roles', [])
                # 检查用户是否有允许的角色
                if any(role in allowed_roles for role in user_roles):
                    # 如果用户有权限，继续执行视图函数
                    return await f(request, *args, **kwargs)
                else:
                    # 如果用户没有权限，返回403禁止访问
                    return resp_failure(403, "您的权限不足以操作")
            else:
                # 返回401未经授权
                return resp_failure(401, "您还未授权，请完善资料。")

        return decorated_function

    return decorator


def check_authorize(exclude_staff: bool = False):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # 假设request.ctx.user是一个用户对象，包含phone属性
            user_phone = getattr(request.ctx.user, 'phone')
            nickname = getattr(request.ctx.user, 'nickname')
            # 检查用户是否有手机号
            if user_phone and nickname:
                if not exclude_staff:
                    return await f(request, *args, **kwargs)
                else:
                    user_roles = getattr(request.ctx.user, 'staff_roles', [])
                    if not user_roles:
                        return await f(request, *args, **kwargs)
                    else:
                        return resp_failure(403, "您的权限不足以操作")
            else:
                # 返回401未经授权
                return resp_failure(401, "您还未授权，请完善资料。")

        return decorated_function

    return decorator
