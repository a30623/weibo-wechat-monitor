import os
import re
import sys
from pathlib import Path

import yaml


def required_secret(name):
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"缺少 GitHub Actions Secret：{name}", file=sys.stderr)
        raise SystemExit(2)
    return value


def main():
    uid = required_secret("WEIBO_UID")
    if not re.fullmatch(r"\d+", uid):
        print("WEIBO_UID 必须是纯数字", file=sys.stderr)
        raise SystemExit(2)

    config = {
        "common": {
            "proxy_pool": {"enable": False, "proxy_pool_url": ""},
            "push_channel": {"send_test_msg_when_start": False},
        },
        "query_task": [{
            "name": "博主A微博监控",
            "enable": True,
            "type": "weibo",
            "intervals_second": 300,
            "jitter_seconds": 30,
            "begin_time": "00:00",
            "end_time": "23:59",
            "target_push_name_list": ["Server酱 Turbo"],
            "enable_dynamic_check": True,
            "enable_living_check": False,
            "uid_list": [uid],
            "api_mode": "desktop",
            "cookie": required_secret("WEIBO_COOKIE"),
            "state_file": "data/weibo_state.json",
        }],
        "push_channel": [{
            "name": "Server酱 Turbo",
            "enable": True,
            "type": "serverChan_turbo",
            "send_key": required_secret("SERVERCHAN_SENDKEY"),
        }],
    }

    output = Path(os.environ.get("AIO_CONFIG_FILE", "config.local.yml"))
    output.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("云端私密配置已生成（凭据内容未输出）")


if __name__ == "__main__":
    main()
