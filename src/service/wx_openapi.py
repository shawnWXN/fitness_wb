import requests

from infra.utils import requests_retry


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


def send_subscribe_message(template_id: str, data: dict, receiver: str):
    response: requests.Response = requests_retry(
        'post', 'http://api.weixin.qq.com/cgi-bin/message/subscribe/send',
        json={
            "touser": receiver,
            "template_id": template_id,
            "page": "index",
            "miniprogram_state": "trial",
            "lang": "zh_CN",
            "data": data
        }
    )
    resp_dict = response.json()
    assert resp_dict.get('errcode') == 0, str(resp_dict)
