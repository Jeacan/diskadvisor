"""大文件扫描器。"""

from __future__ import annotations

import os
from pathlib import Path

from loguru import logger

from diskadvisor.core.models import BigFile, SystemSnapshot
from diskadvisor.scanner.base import BaseScanner


class BigFileScanner(BaseScanner[list[BigFile]]):
    """扫描大文件。"""

    name = "big_file"

    DEFAULT_ROOTS = [
        "%USERPROFILE%\\Downloads",
        "%USERPROFILE%\\Documents",
        "%USERPROFILE%\\Desktop",
        "%USERPROFILE%\\Videos",
    ]

    # 跳过这些系统目录
    SKIP_DIRS = {
        "AppData",
        ".git",
        "node_modules",
        "__pycache__",
        "Windows",
        "$Recycle.Bin",
    }

    def __init__(
        self,
        roots: list[str] | None = None,
        threshold_gb: float = 0.5,
        max_results: int = 20,
        max_depth: int = 5,
    ) -> None:
        """
        Args:
            roots: 扫描根目录。
            threshold_gb: 大文件阈值（GB）。
            max_results: 最多返回数量。
            max_depth: 最大递归深度。
        """
        self.roots = roots or self.DEFAULT_ROOTS
        self.threshold_bytes = int(threshold_gb * 1024**3)
        self.max_results = max_results
        self.max_depth = max_depth

    def scan(self) -> list[BigFile]:
        """扫描大文件。"""
        results: list[BigFile] = []

        for root in self.roots:
            expanded = os.path.expandvars(root)
            if not Path(expanded).exists():
                continue

            try:
                results.extend(self._scan_root(expanded))
            except Exception as e:
                logger.debug("扫描大文件失败：{} - {}", expanded, e)

        results.sort(key=lambda f: f.size_gb, reverse=True)
        return results[: self.max_results]

    def apply(self, snapshot: SystemSnapshot, result: list[BigFile]) -> None:
        snapshot.big_files = result

    def _scan_root(self, root: str) -> list[BigFile]:
        """扫描单个根目录下的大文件。"""
        results: list[BigFile] = []
        stack: list[tuple[Path, int]] = [(Path(root), 0)]

        while stack:
            current, depth = stack.pop()
            if depth > self.max_depth:
                continue

            try:
                for entry in current.iterdir():
                    try:
                        if entry.is_dir():
                            if entry.name in self.SKIP_DIRS:
                                continue
                            stack.append((entry, depth + 1))
                        elif entry.is_file():
                            size = entry.stat().st_size
                            if size >= self.threshold_bytes:
                                results.append(
                                    BigFile(
                                        path=str(entry),
                                        size_gb=round(size / (1024**3), 2),
                                    )
                                )
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError):
                continue

        return results