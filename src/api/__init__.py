from sanic.request import Request
from tortoise.queryset import QuerySet

from common.const import CONST


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
        'pages': (1 if count else 0) if count <= page_size else (count // page_size if count % page_size else count // page_size + 1),
        'items': items
    }
