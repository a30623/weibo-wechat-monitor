import json
import os
from pathlib import Path

from common.logger import log


class JsonStateStore:
    """Small atomic JSON store for persistent per-task deduplication state."""

    def __init__(self, state_file="data/state.json"):
        self.path = Path(state_file)
        self._data = self._load()

    def _load(self):
        if not self.path.exists():
            return {"version": 1, "weibo": {}}
        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("state root must be an object")
            data.setdefault("version", 1)
            data.setdefault("weibo", {})
            return data
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise RuntimeError(f"无法读取状态文件 {self.path}: {type(error).__name__}") from error

    def has_weibo_baseline(self, task_name, uid):
        return str(uid) in self._data["weibo"].get(task_name, {})

    def get_weibo_seen(self, task_name, uid):
        return list(self._data["weibo"].get(task_name, {}).get(str(uid), []))

    def set_weibo_seen(self, task_name, uid, ids):
        tasks = self._data["weibo"].setdefault(task_name, {})
        tasks[str(uid)] = list(ids)
        self._save()

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(self._data, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, self.path)
        log.info(f"去重状态已持久化: {self.path}")
