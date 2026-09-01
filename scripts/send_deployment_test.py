import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from push_channel.server_chan_turbo import ServerChanTurbo


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.local.yml"
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    channel_config = next(item for item in config["push_channel"]
                          if item.get("enable") and item.get("type") == "serverChan_turbo")
    channel = ServerChanTurbo(channel_config)
    success = channel.push(
        title="微博监控部署测试",
        content="微博监控已完成配置，Server酱 Turbo 通道验证消息。",
        jump_url="https://sct.ftqq.com",
    )
    if not success:
        print("Server酱测试消息发送失败（响应内容未输出）", file=sys.stderr)
        raise SystemExit(1)
    print("Server酱测试消息发送成功（响应内容未输出）")


if __name__ == "__main__":
    main()
