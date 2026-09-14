from __future__ import annotations

import copy
from pathlib import Path

import yaml


PROJECT_DIR = Path(__file__).resolve().parent.parent
SOURCE = PROJECT_DIR / "config.local.yml"
DESTINATION = PROJECT_DIR / "config.wechat.local.yml"


def main() -> None:
    if DESTINATION.exists():
        raise SystemExit(
            "config.wechat.local.yml already exists; refusing to overwrite private values."
        )

    config = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    tasks = config.get("query_task") or []
    weibo_tasks = [task for task in tasks if task.get("type") == "weibo"]
    if not weibo_tasks:
        raise SystemExit("No Weibo task was found in config.local.yml.")

    task = copy.deepcopy(weibo_tasks[0])
    task.update(
        {
            "name": "博主A微博监控",
            "enable": True,
            "intervals_second": 300,
            "jitter_seconds": 30,
            "begin_time": "00:00",
            "end_time": "23:59",
            "target_push_name_list": ["微信公众号"],
            "enable_dynamic_check": True,
            "enable_living_check": False,
            "api_mode": "desktop",
            "state_file": "data/weibo_state.json",
        }
    )

    output = {
        "common": copy.deepcopy(config.get("common") or {}),
        "query_task": [task],
        "push_channel": [
            {
                "name": "微信公众号",
                "enable": True,
                "type": "wechat_official_account",
                "app_id": "<WECHAT_APP_ID>",
                "app_secret": "<WECHAT_APP_SECRET>",
                "template_id": "<WECHAT_TEMPLATE_ID>",
                "open_id_list": ["<WECHAT_OPEN_ID>"],
            }
        ],
    }
    output["common"]["push_channel"] = {"send_test_msg_when_start": False}

    rendered = yaml.safe_dump(
        output,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    DESTINATION.write_text(rendered, encoding="utf-8", newline="\n")
    print("Prepared ignored WeChat local configuration (private values not displayed).")


if __name__ == "__main__":
    main()
