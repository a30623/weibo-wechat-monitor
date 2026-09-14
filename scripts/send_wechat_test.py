import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

config_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config.wechat.local.yml").resolve()
os.environ["AIO_CONFIG_FILE"] = str(config_path)

import push_channel
from common.config import global_config


def main():
    configs = [item for item in global_config.get_push_channel_config()
               if item.get("enable") and item.get("type") == "wechat_official_account"]
    if len(configs) != 1:
        print("应恰好启用一个微信公众号推送通道", file=sys.stderr)
        raise SystemExit(2)
    channel = push_channel.get_push_channel(configs[0])
    if not channel.push(
            "微博监控公众号部署测试",
            "微信公众号模板消息通道连接成功。正式监控首次启动只建立基线，不发送历史微博。"):
        raise SystemExit(1)
    print("微信公众号测试消息发送成功（凭据内容未输出）")


if __name__ == "__main__":
    main()
