"""扫描结果缓存。"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from diskadvisor.core.config import Settings
from diskadvisor.core.models import SystemSnapshot


@dataclass
class _CacheEntry:
    snapshot: SystemSnapshot
    timestamp: float


class SnapshotCache:
    """扫描结果缓存。

    以 (no_deep, top_n, threshold) 为 key，TTL 默认 300 秒。
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = ttl_seconds
        self._cache: dict[tuple, _CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: tuple) -> SystemSnapshot | None:
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            if time.time() - entry.timestamp > self.ttl:
                del self._cache[key]
                return None
            return entry.snapshot

    def set(self, key: tuple, snapshot: SystemSnapshot) -> None:
        with self._lock:
            self._cache[key] = _CacheEntry(snapshot=snapshot, timestamp=time.time())

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


_cache = SnapshotCache()


def make_key(settings: Settings, no_deep: bool) -> tuple:
    """生成缓存 key。"""
    return (no_deep, settings.top_dir_count, settings.big_file_threshold_gb)


def get_cache() -> SnapshotCache:
    return _cache