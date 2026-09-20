"""LRU cache for downloaded files."""
import json
import shutil
import time
from collections import OrderedDict
from pathlib import Path

from . import config

CACHE_DIR = config.CONFIG_DIR / "cache"
CACHE_INDEX = CACHE_DIR / "index.json"
MAX_CACHE_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB


class LRUCache:
    def __init__(self, max_size=MAX_CACHE_SIZE):
        self.max_size = max_size
        self.cache = OrderedDict()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_index()

    def _load_index(self):
        if not CACHE_INDEX.exists():
            return
        try:
            with open(CACHE_INDEX, encoding="utf-8") as f:
                data = json.load(f)
            for key, info in data.items():
                p = Path(info["path"])
                if p.exists():
                    self.cache[key] = {
                        "path": p,
                        "size": info["size"],
                        "last_used": info.get("last_used", time.time()),
                    }
        except (json.JSONDecodeError, IOError, KeyError):
            pass

    def _save_index(self):
        data = {
            k: {
                "path": str(v["path"]),
                "size": v["size"],
                "last_used": v["last_used"],
            }
            for k, v in self.cache.items()
        }
        try:
            with open(CACHE_INDEX, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def _total_size(self):
        return sum(v["size"] for v in self.cache.values())

    def get(self, key):
        if key not in self.cache:
            return None
        info = self.cache.pop(key)
        info["last_used"] = time.time()
        self.cache[key] = info
        self._save_index()
        return info["path"] if info["path"].exists() else None

    def put(self, key, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            return
        size = file_path.stat().st_size
        if key in self.cache:
            self._remove_entry(key)
        while self._total_size() + size > self.max_size and self.cache:
            self._remove_oldest()
        cache_path = CACHE_DIR / file_path.name
        try:
            shutil.copy2(file_path, cache_path)
        except OSError:
            return
        self.cache[key] = {
            "path": cache_path,
            "size": size,
            "last_used": time.time(),
        }
        self._save_index()

    def _remove_entry(self, key):
        info = self.cache.pop(key, None)
        if info:
            try:
                info["path"].unlink(missing_ok=True)
            except OSError:
                pass

    def _remove_oldest(self):
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove_entry(oldest_key)

    def clear(self):
        count = 0
        size = 0
        for info in self.cache.values():
            try:
                size += info["size"]
                info["path"].unlink(missing_ok=True)
                count += 1
            except OSError:
                pass
        self.cache.clear()
        self._save_index()
        return count, size

    def info(self):
        return {
            "count": len(self.cache),
            "total_size": self._total_size(),
            "max_size": self.max_size,
            "items": [
                {
                    "key": k,
                    "path": str(v["path"]),
                    "size": v["size"],
                    "last_used": v["last_used"],
                }
                for k, v in self.cache.items()
            ],
        }


cache = LRUCache()
