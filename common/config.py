import os

import yaml

from common.logger import log


class ConfigReaderForYml(object):
    def __init__(self, config_file_name=None):
        if config_file_name is None:
            config_file_name = os.environ.get("AIO_CONFIG_FILE", "config.local.yml")
            if not os.path.exists(os.path.join(os.getcwd(), config_file_name)):
                config_file_name = "config.yml"
        config_file_path = os.path.join(os.getcwd(), config_file_name)
        if not os.path.exists(config_file_path):
            raise FileNotFoundError(f"No such file: {config_file_name}")
        with open(config_file_path, "r", encoding="utf-8") as file:
            self._config = yaml.safe_load(file)

    def get_common_config(self) -> dict:
        result = self._config.get("common", {})
        log.info("加载配置 common（内容已脱敏，不输出配置值）")
        return result

    def get_query_task_config(self) -> list:
        result = self._config.get("query_task", [])
        summary = [{"name": item.get("name"), "type": item.get("type"), "enable": item.get("enable", False)}
                   for item in result]
        log.info(f"加载查询任务摘要: {summary}")
        return result

    def get_push_channel_config(self) -> list:
        result = self._config.get("push_channel", [])
        summary = [{"name": item.get("name"), "type": item.get("type"), "enable": item.get("enable", False)}
                   for item in result]
        log.info(f"加载推送通道摘要: {summary}")
        return result


global_config = ConfigReaderForYml()
