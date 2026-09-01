import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import push_channel
import query_task
from common.config import global_config
from common.logger import log
from main import init_push_channel


def main():
    init_push_channel(global_config.get_push_channel_config())
    enabled = [item for item in global_config.get_query_task_config() if item.get("enable", False)]
    if not enabled:
        raise RuntimeError("没有启用的查询任务")
    for config in enabled:
        task = query_task.get_query_task(config)
        result = task.query()
        if result is None or any(item is None for item in result):
            raise RuntimeError(f"查询失败：{config.get('name', '')}")
        log.info(f"单次云端检查完成：{config.get('name', '')}")
    push_channel.push_channel_dict.clear()
    return result


if __name__ == "__main__":
    main()
