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
    assert resp_dict.get('phone_info', {}).get('phoneNumber'), resp_dict.get('errmsg') or 'wx system error'
    return resp_dict.get('phone_info', {}).get('phoneNumber')


if __name__ == '__main__':
    phone_via_code('f0c372b470fc64d4de15b4a4fa8cb33d6f43051b36358a1249835839fd443767')
