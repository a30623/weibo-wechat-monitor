import argparse
import json
import re
import sys
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import requests
import yaml


def resolve_uid(value):
    value = value.strip()
    if value.isdigit():
        return value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or not parsed.hostname.endswith("weibo.com"):
        raise ValueError("请输入 weibo.com 或 m.weibo.cn 的主页链接")
    patterns = (r"/(?:u|profile)/([0-9]+)", r"^/([0-9]+)(?:/|$)")
    for pattern in patterns:
        match = re.search(pattern, parsed.path)
        if match:
            return match.group(1)
    response = requests.get(value, timeout=10)
    response.raise_for_status()
    for pattern in (r'\$CONFIG\[.oid.\]\s*=\s*[.\"]([0-9]+)', r'\"oid\"\s*:\s*\"([0-9]+)\"'):
        match = re.search(pattern, response.text)
        if match:
            return match.group(1)
    raise ValueError("无法从该主页链接解析数字 UID")


def fetch_latest(uid, cookie=""):
    url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}&count=25"
    headers = {"accept": "application/json", "referer": f"https://m.weibo.cn/u/{uid}",
               "x-requested-with": "XMLHttpRequest"}
    if cookie:
        headers["cookie"] = cookie
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    payload = json.loads(response.content.decode("utf-8"))
    cards = [card for card in payload.get("data", {}).get("cards", [])
             if card.get("mblog") and card["mblog"].get("isTop") != 1]
    if not cards:
        raise RuntimeError("公开接口未返回可用微博；可能触发限流或 UID 无效")
    mblog = cards[0]["mblog"]
    created = parsedate_to_datetime(mblog["created_at"]).astimezone().isoformat(timespec="seconds")
    return mblog.get("user", {}).get("screen_name", "未知"), str(mblog["id"]), created


def main():
    parser = argparse.ArgumentParser(description="安全解析微博 UID 并验证最新公开微博（不输出正文/Cookie）")
    parser.add_argument("profile")
    parser.add_argument("--uid-only", action="store_true", help="只解析 UID，不读取微博")
    parser.add_argument("--config", help="从私密配置读取 Cookie 后验证公开微博")
    args = parser.parse_args()
    try:
        uid = resolve_uid(args.profile)
        if args.uid_only:
            print(uid)
            return
        cookie = ""
        if args.config:
            with open(args.config, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
            task = next(item for item in config.get("query_task", [])
                        if item.get("enable") and item.get("type") == "weibo")
            cookie = str(task.get("cookie", ""))
        name, mblog_id, created = fetch_latest(uid, cookie)
    except Exception as error:
        print(f"验证失败：{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"博主名称：{name}")
    print(f"UID：{uid}")
    print(f"最新公开微博时间：{created}")
    print(f"最新公开微博链接：https://m.weibo.cn/detail/{mblog_id}")


if __name__ == "__main__":
    main()
