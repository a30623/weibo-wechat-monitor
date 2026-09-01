import json
import re
import time
from collections import deque
from email.utils import parsedate_to_datetime
from html import unescape

from common import util
from common.logger import log
from common.proxy import my_proxy
from common.state import JsonStateStore
from query_task import QueryTask


class QueryWeibo(QueryTask):
    def __init__(self, config):
        super().__init__(config)
        self.uid_list = config.get("uid_list", [])
        self.cookie = config.get("cookie", "")
        self.api_mode = config.get("api_mode", "mobile")
        self.state_store = JsonStateStore(config.get("state_file", "data/weibo_state.json"))

    def query(self):
        if not self.enable:
            return []
        try:
            results = []
            current_time = time.strftime("%H:%M", time.localtime(time.time()))
            if self.begin_time <= current_time <= self.end_time:
                my_proxy.current_proxy_ip = my_proxy.get_proxy(proxy_check_url="https://m.weibo.com")
                if self.enable_dynamic_check:
                    for uid in self.uid_list:
                        results.append(self.query_dynamic(uid))
            return results
        except Exception as error:
            log.error(f"【微博-查询任务-{self.name}】出错：{type(error).__name__}", exc_info=True)
            return None

    def query_dynamic(self, uid=None):
        if uid is None:
            return None
        uid = str(uid)
        if self.api_mode == "desktop":
            query_url = f"https://weibo.com/ajax/statuses/mymblog?uid={uid}&page=1&feature=0"
            headers = self.get_desktop_headers(uid)
        else:
            query_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}&count=25"
            headers = self.get_headers(uid)
        if self.cookie:
            headers["cookie"] = self.cookie
        response = util.requests_get(query_url, f"微博-查询动态状态-{self.name}", headers=headers, use_proxy=True)
        if not util.check_response_is_ok(response):
            return None

        try:
            result = json.loads(response.content.decode("utf-8"))
            if result.get("ok") != 1 or not isinstance(result.get("data"), dict):
                log.error(f"【微博-查询动态状态-{self.name}】接口业务状态异常，可能需要更新 Cookie（响应内容已隐藏）")
                return None
            if self.api_mode == "desktop":
                cards = [{"card_type": 9, "mblog": item}
                         for item in result["data"].get("list", [])]
            else:
                cards = result["data"].get("cards", [])
        except (ValueError, AttributeError, UnicodeDecodeError):
            log.error(f"【微博-查询动态状态-{self.name}】响应不是有效 JSON，uid：{uid}")
            return None

        cards = [card for card in cards if card.get("mblog") is not None
                 and card["mblog"].get("isTop") != 1
                 and card["mblog"].get("mblogtype") != 2]

        if not cards:
            if not self.state_store.has_weibo_baseline(self.name, uid):
                self.state_store.set_weibo_seen(self.name, uid, ["-1"])
                log.info(f"【微博-查询动态状态-{self.name}】【uid:{uid}】已建立空动态基线")
            else:
                log.warning(f"【微博-查询动态状态-{self.name}】【uid:{uid}】动态列表为空")
            return {"uid": uid, "screen_name": None, "latest_id": None, "new_count": 0}

        latest_mblog = cards[0]["mblog"]
        screen_name = latest_mblog.get("user", {}).get("screen_name", uid)
        current_ids = [str(card["mblog"]["id"]) for card in cards]

        # A missing state entry means this is the first successful read. Store every
        # currently visible item as the baseline and deliberately send nothing.
        if not self.state_store.has_weibo_baseline(self.name, uid):
            self.dynamic_dict[uid] = deque(current_ids, maxlen=self.len_of_deque)
            self.state_store.set_weibo_seen(self.name, uid, self.dynamic_dict[uid])
            log.info(f"【微博-查询动态状态-{self.name}】【{screen_name}】首次基线已建立，共 {len(current_ids)} 条，不推送历史微博")
            return {"uid": uid, "screen_name": screen_name, "latest_id": current_ids[0], "new_count": 0}

        if uid not in self.dynamic_dict:
            stored_ids = self.state_store.get_weibo_seen(self.name, uid)
            self.dynamic_dict[uid] = deque(stored_ids, maxlen=self.len_of_deque)

        unseen_cards = [card for card in cards if str(card["mblog"]["id"]) not in self.dynamic_dict[uid]]
        pushed_count = 0
        # API order is newest first. Send oldest unseen first for natural chronology.
        for card in reversed(unseen_cards):
            mblog_id = str(card["mblog"]["id"])
            handled = self._handle_new_card(card, screen_name)
            if handled:
                self.dynamic_dict[uid].append(mblog_id)
                self.state_store.set_weibo_seen(self.name, uid, self.dynamic_dict[uid])
                pushed_count += 1

        log.info(f"【微博-查询动态状态-{self.name}】【{screen_name}】查询成功，本次新增 {pushed_count} 条")
        return {"uid": uid, "screen_name": screen_name, "latest_id": current_ids[0], "new_count": pushed_count}

    def _handle_new_card(self, card, fallback_screen_name):
        if card.get("card_type") != 9:
            log.info(f"【微博-查询动态状态-{self.name}】发现非微博卡片，记录后不推送")
            return True

        mblog = card["mblog"]
        mblog_id = str(mblog["id"])
        user = mblog.get("user", {})
        screen_name = user.get("screen_name", fallback_screen_name)
        avatar_url = user.get("avatar_hd")
        content = self._extract_content(mblog)
        pic_url = self._extract_picture(mblog)
        jump_url = f"https://m.weibo.cn/detail/{mblog_id}"
        try:
            created_at = parsedate_to_datetime(mblog["created_at"]).astimezone()
            dynamic_time = created_at.strftime("%Y-%m-%d %H:%M:%S %z")
        except (KeyError, TypeError, ValueError):
            dynamic_time = str(mblog.get("created_at", "未知"))

        log.info(f"【微博-查询动态状态-{self.name}】【{screen_name}】发现新微博，准备推送（正文不写日志）")
        return self.push_for_weibo_dynamic(
            screen_name, mblog_id, content, pic_url, jump_url, dynamic_time,
            dynamic_raw_data=card, avatar_url=avatar_url)

    @staticmethod
    def _plain_text(value):
        return unescape(re.sub(r"<[^>]+>", "", value or "")).strip()

    @classmethod
    def _extract_content(cls, mblog):
        text = cls._plain_text(mblog.get("raw_text") or mblog.get("text_raw") or mblog.get("text"))
        forwarded = mblog.get("retweeted_status")
        if forwarded:
            forwarded_user = forwarded.get("user", {}).get("screen_name", "原博主")
            forwarded_text = cls._plain_text(
                forwarded.get("raw_text") or forwarded.get("text_raw") or forwarded.get("text"))
            text = f"{text}\n\n转发自 @{forwarded_user}：{forwarded_text}".strip()
        return text or "（无文字内容）"

    @staticmethod
    def _extract_picture(mblog):
        for source in (mblog, mblog.get("retweeted_status") or {}):
            if source.get("original_pic"):
                return source["original_pic"]
            pics = source.get("pics") or []
            if pics:
                return pics[0].get("large", {}).get("url") or pics[0].get("url")
            pic_infos = source.get("pic_infos") or {}
            if pic_infos:
                first = next(iter(pic_infos.values()))
                return (first.get("large") or first.get("original") or {}).get("url")
        return None

    @staticmethod
    def get_headers(uid):
        return {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "mweibo-pwa": "1",
            "referer": f"https://m.weibo.cn/u/{uid}",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-requested-with": "XMLHttpRequest",
        }

    @staticmethod
    def get_desktop_headers(uid):
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "referer": f"https://weibo.com/u/{uid}",
            "x-requested-with": "XMLHttpRequest",
        }

    def push_for_weibo_dynamic(self, username=None, mblog_id=None, content=None, pic_url=None,
                                jump_url=None, dynamic_time=None, dynamic_raw_data=None, avatar_url=None):
        if username is None or mblog_id is None or content is None:
            log.error(f"【微博-动态提醒推送-{self.name}】缺少必要参数（参数内容已隐藏）")
            return False
        summary = content[:300] + ("..." if len(content) > 300 else "")
        title = f"【微博】【{username}】发布了新微博"
        message = (f"博主：{username}\n\n正文：{summary}\n\n"
                   f"发布时间：{dynamic_time}\n\n原微博：{jump_url}")
        extend_data = {"dynamic_raw_data": dynamic_raw_data, "avatar_url": avatar_url}
        return super().push(title, message, jump_url, pic_url, extend_data=extend_data)
