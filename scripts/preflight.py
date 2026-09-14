import sys
from pathlib import Path

import yaml


def fail(message):
    print(f"配置检查失败：{message}", file=sys.stderr)
    raise SystemExit(2)


def main():
    config_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config.local.yml")
    if not config_path.is_file():
        fail(f"找不到 {config_path}")
    try:
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except (OSError, yaml.YAMLError) as error:
        fail(f"YAML 无法解析（{type(error).__name__}）")

    tasks = [item for item in config.get("query_task", []) if item.get("enable")]
    if len(tasks) != 1 or tasks[0].get("type") != "weibo":
        fail("应恰好启用一个微博任务")
    task = tasks[0]
    uids = [str(uid).strip() for uid in task.get("uid_list", [])]
    if len(uids) != 1 or not uids[0].isdigit():
        fail("请把 <WEIBO_UID> 替换为微博数字 UID")
    if int(task.get("intervals_second", 0)) != 300:
        fail("检查间隔必须为 300 秒")
    if int(task.get("jitter_seconds", 0)) < 0:
        fail("抖动不能为负数")
    cookie = str(task.get("cookie", "")).strip()
    if not cookie or "WEIBO_COOKIE" in cookie or cookie.startswith("<"):
        fail("当前网络验证需要微博 Cookie；请只写入私密配置，不要粘贴到聊天或命令行")

    channels = [item for item in config.get("push_channel", []) if item.get("enable")]
    if len(channels) != 1:
        fail("应恰好启用一个推送通道")
    channel = channels[0]
    if channel.get("name") not in task.get("target_push_name_list", []):
        fail("查询任务绑定的推送通道名称与已启用通道不一致")
    if channel.get("type") == "serverChan_turbo":
        send_key = str(channel.get("send_key", "")).strip()
        if not send_key or "SERVERCHAN_SENDKEY" in send_key or send_key.startswith("<"):
            fail("请在私密配置中填写 Server酱 Turbo SendKey")
    elif channel.get("type") == "wechat_official_account":
        required = {
            "app_id": "AppID",
            "app_secret": "AppSecret",
            "template_id": "模板 ID",
        }
        for key, label in required.items():
            value = str(channel.get(key, "")).strip()
            if not value or value.startswith("<"):
                fail(f"请在私密配置中填写微信公众号 {label}")
        open_ids = channel.get("open_id_list", channel.get("open_id", []))
        if isinstance(open_ids, str):
            open_ids = [open_ids]
        if not open_ids or any(not str(value).strip() or str(value).startswith("<") for value in open_ids):
            fail("请在私密配置中填写至少一个微信公众号接收者 OpenID")
    else:
        fail(f"当前部署检查不支持推送类型：{channel.get('type')}")
    print("配置检查通过（凭据内容未输出）")


if __name__ == "__main__":
    main()
