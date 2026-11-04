"""共享依赖。"""

from __future__ import annotations

import ctypes
import os
import platform

from diskadvisor.core.config import Settings
from diskadvisor.core.models import SystemSnapshot
from diskadvisor.scanner import (
    BigFileScanner,
    DirSizeScanner,
    DiskScanner,
    EnvScanner,
    SoftwareScanner,
)
from diskadvisor.server.cache import get_cache, make_key


def collect_snapshot(
    settings: Settings,
    no_deep: bool = False,
    *,
    force_refresh: bool = False,
) -> SystemSnapshot:
    """采集系统快照（带缓存）。"""
    cache = get_cache()
    key = make_key(settings, no_deep)

    if not force_refresh:
        cached = cache.get(key)
        if cached is not None:
            return cached

    snapshot = SystemSnapshot(
        os_version=platform.platform(),
        os_build=platform.version(),
        user_profile=os.environ.get("USERPROFILE", ""),
        computer_name=platform.node(),
        is_admin=_is_admin(),
    )

    scanners: list = [
        DiskScanner(),
        EnvScanner(),
        SoftwareScanner(),
    ]

    if not no_deep:
        scanners.append(DirSizeScanner(top_n=settings.top_dir_count))
        scanners.append(BigFileScanner(threshold_gb=settings.big_file_threshold_gb))

    for scanner in scanners:
        scanner.run(snapshot)

    cache.set(key, snapshot)
    return snapshot


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except Exception:
        return False