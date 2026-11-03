"""目录占用扫描器。"""

from __future__ import annotations

import os
from pathlib import Path

from loguru import logger

from diskadvisor.core.models import DirSize, SystemSnapshot
from diskadvisor.scanner.base import BaseScanner


class DirSizeScanner(BaseScanner[list[DirSize]]):
    """扫描指定根目录下的一级子目录占用。

    只扫描一级子目录，避免递归过深导致扫描时间失控。
    """

    name = "dir_size"

    # 默认扫描的根目录
    DEFAULT_ROOTS = [
        "%USERPROFILE%",
        "%USERPROFILE%\\AppData\\Local",
        "%USERPROFILE%\\AppData\\Roaming",
        "%USERPROFILE%\\Documents",
        "%USERPROFILE%\\Downloads",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
    ]

    def __init__(
        self,
        roots: list[str] | None = None,
        top_n: int = 10,
        min_size_gb: float = 0.05,
    ) -> None:
        """
        Args:
            roots: 扫描根目录列表，默认为 DEFAULT_ROOTS。
            top_n: 返回 Top N 大目录。
            min_size_gb: 最小目录大小阈值（GB），低于此值不返回。
        """
        self.roots = roots or self.DEFAULT_ROOTS
        self.top_n = top_n
        self.min_size_gb = min_size_gb

    def scan(self) -> list[DirSize]:
        """扫描目录占用。"""
        results: list[DirSize] = []

        for root in self.roots:
            expanded = os.path.expandvars(root)
            if not Path(expanded).exists():
                continue

            try:
                subdirs = self._scan_root(expanded)
                results.extend(subdirs)
            except Exception as e:
                logger.debug("扫描目录失败：{} - {}", expanded, e)

        # 按大小降序，取 Top N
        results.sort(key=lambda d: d.size_gb, reverse=True)
        return results[: self.top_n]

    def apply(self, snapshot: SystemSnapshot, result: list[DirSize]) -> None:
        snapshot.top_dirs = result

    def _scan_root(self, root: str) -> list[DirSize]:
        """扫描单个根目录下的一级子目录。"""
        results: list[DirSize] = []
        root_path = Path(root)

        try:
            entries = list(root_path.iterdir())
        except PermissionError:
            logger.debug("无权限访问：{}", root)
            return []

        for entry in entries:
            if not entry.is_dir():
                continue

            try:
                size_bytes, file_count = self._dir_size(entry)
            except Exception as e:
                logger.debug("计算目录大小失败：{} - {}", entry, e)
                continue

            size_gb = round(size_bytes / (1024**3), 2)
            if size_gb < self.min_size_gb:
                continue

            results.append(
                DirSize(
                    path=str(entry),
                    size_gb=size_gb,
                    file_count=file_count,
                )
            )

        return results

    @staticmethod
    def _dir_size(path: Path, max_depth: int = 10) -> tuple[int, int]:
        """递归计算目录大小和文件数。

        Args:
            path: 目录路径。
            max_depth: 最大递归深度，防止过深。

        Returns:
            (总字节数, 文件数)
        """
        total_bytes = 0
        file_count = 0

        stack: list[tuple[Path, int]] = [(path, 0)]
        while stack:
            current, depth = stack.pop()
            if depth > max_depth:
                continue

            try:
                for entry in current.iterdir():
                    try:
                        if entry.is_file():
                            total_bytes += entry.stat().st_size
                            file_count += 1
                        elif entry.is_dir():
                            stack.append((entry, depth + 1))
                    except (PermissionError, OSError):
                        continue
            except (PermissionError, OSError):
                continue

        return total_bytes, file_count