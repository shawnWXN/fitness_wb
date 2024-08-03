import requests

from common.const import CONST
from infra.utils import requests_retry
from loggers.logger import logger


def phone_via_code(code: str) -> str:
    """
    {
        "errcode": 0,
        "errmsg": "ok",
        "phone_info": {
            "phoneNumber": "xxxxxx",
            "purePhoneNumber": "xxxxxx",
            "countryCode": 86,
            "watermark": {
                "timestamp": 1637744274,
                "appid": "xxxx"
            }
        }
    }
    """
    response: requests.Response = requests_retry(
        'post', 'http://api.weixin.qq.com/wxa/business/getuserphonenumber',
        json={'code': code}
    )
    resp_dict = response.json()
    assert resp_dict.get('phone_info', {}).get('phoneNumber'), str(resp_dict)
    return resp_dict.get('phone_info', {}).get('phoneNumber')


def subscribe_send(openid: str, template_id: str, template_data: dict) -> bool:
    """
    reference: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/mp-message-management/subscribe-message/sendMessage.html
    """
    payload = {
        "touser": openid,
        "template_id": template_id,
        "data": template_data,
    }
    if template_id == CONST.ORDER_STATUS_TEMPLATE:
        """Example
        payload['data'] = {
            "phrase1": {
                "value": "三天后到期"
            },
            "thing2": {
                "value": "自寻月卡"
            },
            "time3": {
                "value": "2024年8月26日 21:48"
            },
            "character_string4": {
                "value": 'bFGP8SL7bqZtix9dkj9X4y'
            }
        }"""
        payload['page'] = 'projects/workfit/pages/my/course/my_course'
    else:
        logger.error(f'Unsupported subscribe template {template_id}')
        return False

    # FIXME mock
    # r = random.randint(0, 2)
    # if not r:
    #     response = requests.Response()
    #     response.status_code = 200
    #     response.headers = {'Content-Type': 'application/json'}
    #     response._content = json.dumps({'errcode': 0, 'errmsg': 'ok'}).encode()
    # elif r == 1:
    #     response = requests.Response()
    #     response.status_code = 200
    #     response.headers = {'Content-Type': 'application/json'}
    #     response._content = json.dumps({'errcode': 43101, 'errmsg': 'ok'}).encode()
    # else:
    #     response = requests.Response()
    #     response.status_code = 500
    #     response.headers = {'Content-Type': 'application/json'}
    #     response._content = json.dumps({'errcode': 0, 'errmsg': 'ok'}).encode()

    response: requests.Response = requests_retry(
        'post', 'http://api.weixin.qq.com/cgi-bin/message/subscribe/send', json=payload
    )

    response.raise_for_status()
    errcode = response.json().get('errcode', -1)
    assert errcode in (0, 43101), (f'template={template_id} to {openid} failed, '
                                   f'Response[{response.status_code}] -> {response.text}')
    return False if errcode else True  # 为零发送成功，非零则是用户拒绝订阅消息
