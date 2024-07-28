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


def send_api(openid, template_id):
    url = "http://api.weixin.qq.com/cgi-bin/message/subscribe/send"

    if template_id == 'ErC-bxEn78ABZRpHb_oDhobYc7yOVBEaj7MJBK5akLk':
        payload = {
            "touser": openid,
            "template_id": template_id,
            "miniprogram_state": "developer",
            "data": {
                "thing1": {
                    "value": "三个月包时卡",
                },
                "time3": {
                    "value": "2022年4月26日 21:48",
                },
                "time2": {
                    "value": "2024年8月26日 21:48",
                },
            },
        }
    # i7Ib4M_rAMJ8NABZUqO1Y8Oqqm71NLzrOzAZXypMajA
    else:
        payload = {
            "touser": openid,
            "template_id": template_id,
            "miniprogram_state": "developer",
            "data": {
                "thing1": {
                    "value": "套餐类型1",
                },
                "number3": {
                    "value": 52,
                },
                "number2": {
                    "value": 3
                },
                "thing5": {
                    "value": "这是一个提醒"
                }
            },
        }

    try:
        response: requests.Response = requests_retry('post', url, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        print(f'send_api, Response[{response.status_code}] -> {response.text}')
        return response.json()  # Return the JSON response
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
