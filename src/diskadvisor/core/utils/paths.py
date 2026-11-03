"""路径工具。"""

from __future__ import annotations

from pathlib import Path


def expand_env(path: str) -> str:
    """展开路径中的环境变量（如 %USERPROFILE%）。

    Args:
        path: 原始路径。

    Returns:
        展开后的路径。
    """
    import os

    return os.path.expandvars(path)


def is_subpath(child: str, parent: str) -> bool:
    """判断 child 是否在 parent 之下。

    Args:
        child: 子路径。
        parent: 父路径。

    Returns:
        True 表示 child 在 parent 之下。
    """
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def normalize_path(path: str) -> str:
    """规范化路径：展开环境变量、统一分隔符、去除末尾斜杠。

    Args:
        path: 原始路径。

    Returns:
        规范化后的路径。
    """
    p = expand_env(path).replace("/", "\\").rstrip("\\")
    return p