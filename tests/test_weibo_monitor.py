import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import push_channel
from common.config import ConfigReaderForYml
from common import util
from push_channel.server_chan_turbo import ServerChanTurbo
from query_task.query_weibo import QueryWeibo


class FakeResponse:
    def __init__(self, cards=None, status_code=200, result=None, url="https://m.weibo.cn/api/test", payload=None):
        self.status_code = status_code
        self.url = url
        self.content = json.dumps(payload if payload is not None else
                                  {"ok": 1, "data": {"cards": cards or []}}).encode()
        self._result = result

    def json(self):
        return self._result


class RecordingChannel:
    def __init__(self):
        self.calls = []

    def push(self, title, content, jump_url=None, pic_url=None, extend_data=None):
        self.calls.append({"title": title, "content": content, "jump_url": jump_url, "pic_url": pic_url})
        return True


def card(mblog_id, text="正文", repost=False):
    mblog = {
        "id": str(mblog_id),
        "created_at": "Mon Sep 01 10:00:00 +0800 2026",
        "text": text,
        "raw_text": text,
        "user": {"screen_name": "测试博主", "avatar_hd": "https://img.example/avatar.jpg"},
        "original_pic": "https://img.example/pic.jpg",
    }
    if repost:
        mblog["retweeted_status"] = {
            "text": "原微博正文", "user": {"screen_name": "原博主"},
            "original_pic": "https://img.example/repost.jpg",
        }
    return {"card_type": 9, "scheme": f"sinaweibo://detail/{mblog_id}", "mblog": mblog}


class WeiboMonitorTests(unittest.TestCase):
    def setUp(self):
        push_channel.push_channel_dict.clear()

    def test_baseline_new_item_once_and_restart_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = str(Path(directory) / "state.json")
            config = {
                "name": "博主A微博监控", "enable": True, "type": "weibo",
                "target_push_name_list": ["test"], "enable_dynamic_check": True,
                "uid_list": [123], "state_file": state_file,
            }
            recorder = RecordingChannel()
            push_channel.push_channel_dict["test"] = recorder
            task = QueryWeibo(config)

            with patch("query_task.query_weibo.util.requests_get", return_value=FakeResponse([card("old")])):
                first = task.query_dynamic(123)
            self.assertEqual(first["new_count"], 0)
            self.assertEqual(recorder.calls, [])

            with patch("query_task.query_weibo.util.requests_get",
                       return_value=FakeResponse([card("new", repost=True), card("old")])):
                second = task.query_dynamic(123)
                third = task.query_dynamic(123)
            self.assertEqual(second["new_count"], 1)
            self.assertEqual(third["new_count"], 0)
            self.assertEqual(len(recorder.calls), 1)
            self.assertIn("测试博主", recorder.calls[0]["content"])
            self.assertIn("转发自 @原博主", recorder.calls[0]["content"])
            self.assertIn("发布时间", recorder.calls[0]["content"])
            self.assertEqual(recorder.calls[0]["jump_url"], "https://m.weibo.cn/detail/new")
            self.assertEqual(recorder.calls[0]["pic_url"], "https://img.example/pic.jpg")

            restarted = QueryWeibo(config)
            with patch("query_task.query_weibo.util.requests_get",
                       return_value=FakeResponse([card("new", repost=True), card("old")])):
                after_restart = restarted.query_dynamic(123)
            self.assertEqual(after_restart["new_count"], 0)
            self.assertEqual(len(recorder.calls), 1)

    def test_configuration_logging_redacts_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "private.yml"
            config_path.write_text(
                "common: {secret: TOPSECRET}\nquery_task: []\n"
                "push_channel: [{name: test, type: serverChan_turbo, enable: true, send_key: SCTSECRET}]\n",
                encoding="utf-8")
            with self.assertLogs(level=logging.INFO) as captured:
                reader = ConfigReaderForYml(str(config_path))
                reader.get_common_config()
                reader.get_push_channel_config()
            output = "\n".join(captured.output)
            self.assertNotIn("TOPSECRET", output)
            self.assertNotIn("SCTSECRET", output)

    def test_unauthenticated_response_never_creates_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state.json"
            task = QueryWeibo({
                "name": "博主A微博监控", "enable": True, "type": "weibo",
                "target_push_name_list": ["test"], "enable_dynamic_check": True,
                "uid_list": [123], "state_file": str(state_file),
            })
            response = FakeResponse(payload={"ok": -100, "url": "https://passport.weibo.cn"})
            with patch("query_task.query_weibo.util.requests_get", return_value=response):
                self.assertIsNone(task.query_dynamic(123))
            self.assertFalse(state_file.exists())

    def test_desktop_api_response_establishes_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "state.json"
            task = QueryWeibo({
                "name": "博主A微博监控", "enable": True, "type": "weibo",
                "target_push_name_list": ["test"], "enable_dynamic_check": True,
                "uid_list": [123], "api_mode": "desktop", "cookie": "SUB=hidden",
                "state_file": str(state_file),
            })
            mblog = card("desktop-id")["mblog"]
            mblog["text_raw"] = mblog.pop("raw_text")
            response = FakeResponse(payload={"ok": 1, "data": {"list": [mblog]}})
            with patch("query_task.query_weibo.util.requests_get", return_value=response):
                result = task.query_dynamic(123)
            self.assertEqual(result["latest_id"], "desktop-id")
            self.assertEqual(result["new_count"], 0)
            self.assertTrue(state_file.exists())

    def test_http_error_log_hides_secret_url_path(self):
        response = FakeResponse(status_code=403, url="https://sctapi.ftqq.com/SCT-DO-NOT-LOG.send")
        with self.assertLogs(level=logging.ERROR) as captured:
            self.assertFalse(util.check_response_is_ok(response))
        self.assertNotIn("SCT-DO-NOT-LOG", "\n".join(captured.output))

    def test_server_chan_requires_api_success_code(self):
        channel = ServerChanTurbo({"name": "test", "enable": True, "type": "serverChan_turbo", "send_key": "hidden"})
        with patch("push_channel.server_chan_turbo.util.requests_post",
                   return_value=FakeResponse(result={"code": 0})):
            self.assertTrue(channel.push("title", "body"))
        with patch("push_channel.server_chan_turbo.util.requests_post",
                   return_value=FakeResponse(result={"code": 40001})):
            self.assertFalse(channel.push("title", "body"))


if __name__ == "__main__":
    unittest.main()
