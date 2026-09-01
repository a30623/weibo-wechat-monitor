import requests
from urllib.parse import urlsplit
from fake_useragent import UserAgent

from common.logger import log
from common.proxy import my_proxy

ua = UserAgent(os=["macos"], min_version=120.0)


def _get_random_useragent():
    return ua.chrome


def requests_get(url, module_name="未指定", headers=None, params=None, use_proxy=False):
    if headers is None:
        headers = {}
    random_ua = _get_random_useragent()
    headers.setdefault('User-Agent', random_ua)
    headers.setdefault('user-agent', random_ua)
    proxies = _get_proxy() if use_proxy else None
    try:
        response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=10)
    except Exception as e:
        log.error(f"【{module_name}】请求失败（{type(e).__name__}），未记录请求 URL/请求头")
        return None
    return response


def requests_post(url, module_name="未指定", headers=None, params=None, data=None, json=None, use_proxy=False):
    if headers is None:
        headers = {}
    random_ua = _get_random_useragent()
    headers.setdefault('User-Agent', random_ua)
    headers.setdefault('user-agent', random_ua)
    proxies = _get_proxy() if use_proxy else None
    try:
        response = requests.post(url, headers=headers, params=params, data=data, json=json, proxies=proxies, timeout=10)
    except Exception as e:
        log.error(f"【{module_name}】请求失败（{type(e).__name__}），未记录请求 URL/请求头")
        return None
    return response


def _get_proxy():
    proxy_ip = my_proxy.current_proxy_ip
    if proxy_ip is None:
        return None
    else:
        return {
            "http": f"http://{proxy_ip}"
        }


def check_response_is_ok(response=None):
    if response is None:
        return False
    if response.status_code != requests.codes.OK:
        host = urlsplit(response.url).hostname or "unknown-host"
        log.error(f"HTTP 状态异常: {response.status_code}, host: {host}（URL 路径已隐藏）")
        return False
    return True
