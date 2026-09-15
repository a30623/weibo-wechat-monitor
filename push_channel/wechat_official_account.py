import time

from common import util
from common.logger import log
from . import PushChannel


class WechatOfficialAccount(PushChannel):
    """Push through the official WeChat Official Account template-message API."""

    TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/stable_token"
    SEND_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"
    TOKEN_ERROR_CODES = {40014, 42001}

    def __init__(self, config):
        super().__init__(config)
        self.app_id = str(config.get("app_id", "")).strip()
        self.app_secret = str(config.get("app_secret", "")).strip()
        self.template_id = str(config.get("template_id", "")).strip()
        configured_open_ids = config.get("open_id_list", config.get("open_id", []))
        if isinstance(configured_open_ids, str):
            configured_open_ids = [configured_open_ids]
        self.open_id_list = [str(item).strip() for item in configured_open_ids if str(item).strip()]
        self._access_token = None
        self._token_expires_at = 0

        if not all((self.app_id, self.app_secret, self.template_id, self.open_id_list)):
            log.error(f"【推送_{self.name}】配置不完整，公众号模板消息将无法使用")

    def _get_access_token(self, force_refresh=False):
        now = time.time()
        if not force_refresh and self._access_token and now < self._token_expires_at:
            return self._access_token

        body = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
            "force_refresh": bool(force_refresh),
        }
        response = util.requests_post(self.TOKEN_URL, f"{self.name}_获取公众号access_token", json=body)
        if not util.check_response_is_ok(response):
            return None
        try:
            result = response.json()
        except (TypeError, ValueError):
            log.error(f"【推送_{self.name}】公众号 access_token 响应不是有效 JSON")
            return None

        token = result.get("access_token")
        if not token:
            log.error(f"【推送_{self.name}】获取公众号 access_token 失败，错误码：{result.get('errcode', 'unknown')}")
            return None
        self._access_token = str(token)
        # Refresh five minutes early; the platform normally returns 7200 seconds.
        self._token_expires_at = now + max(60, int(result.get("expires_in", 7200)) - 300)
        return self._access_token

    def _send_one(self, open_id, title, content, jump_url, force_refresh=False):
        access_token = self._get_access_token(force_refresh=force_refresh)
        if not access_token:
            return False
        body = {
            "touser": open_id,
            "template_id": self.template_id,
            "data": {
                "title": {"value": title},
                "content": {"value": content},
                "remark": {"value": "点击消息查看原微博" if jump_url else ""},
            },
        }
        if jump_url:
            body["url"] = jump_url
        response = util.requests_post(
            self.SEND_URL,
            f"{self.name}_发送公众号模板消息",
            params={"access_token": access_token},
            json=body,
        )
        if not util.check_response_is_ok(response):
            return False
        try:
            result = response.json()
        except (TypeError, ValueError):
            log.error(f"【推送_{self.name}】公众号模板消息响应不是有效 JSON")
            return False

        error_code = int(result.get("errcode", -1))
        if error_code in self.TOKEN_ERROR_CODES and not force_refresh:
            self._access_token = None
            self._token_expires_at = 0
            return self._send_one(open_id, title, content, jump_url, force_refresh=True)
        if error_code != 0:
            log.error(f"【推送_{self.name}】公众号模板消息发送失败，错误码：{error_code}")
            return False
        return True

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        if not all((self.app_id, self.app_secret, self.template_id, self.open_id_list)):
            return False
        if pic_url:
            content = f"{content}\n\n微博图片：{pic_url}"
        results = [self._send_one(open_id, title, content, jump_url) for open_id in self.open_id_list]
        success = bool(results) and all(results)
        log.info(f"【推送_{self.name}】{'成功' if success else '失败'}")
        return success
