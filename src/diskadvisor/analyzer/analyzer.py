"""分析器。"""

from __future__ import annotations

import os

from loguru import logger

from diskadvisor.analyzer.models import (
    AnalysisResult,
    DiskPressure,
    MisplacedSoftware,
    PressureLevel,
    SpaceAttribution,
)
from diskadvisor.core.models import SystemSnapshot
from diskadvisor.core.utils.paths import is_subpath, normalize_path
from diskadvisor.kb import KnowledgeBase


class Analyzer:
    """分析系统快照。"""

    def __init__(self, kb: KnowledgeBase | None = None) -> None:
        self.kb = kb or KnowledgeBase()

    def analyze(self, snapshot: SystemSnapshot) -> AnalysisResult:
        """分析快照。"""
        result = AnalysisResult()
        result.disk_pressures = self._analyze_disks(snapshot)
        result.attributions = self._attribute_space(snapshot)
        result.misplaced = self._find_misplaced(snapshot)
        result.env_issues = self._check_env(snapshot)
        return result

    def _analyze_disks(self, snapshot: SystemSnapshot) -> list[DiskPressure]:
        """分析磁盘压力。"""
        pressures: list[DiskPressure] = []

        for disk in snapshot.disks:
            if disk.used_percent >= 90:
                level = PressureLevel.CRITICAL
                message = f"{disk.letter} 盘空间严重不足（剩余 {disk.free_gb:.1f} GB）"
            elif disk.used_percent >= 75:
                level = PressureLevel.WARNING
                message = f"{disk.letter} 盘空间偏紧（剩余 {disk.free_gb:.1f} GB）"
            else:
                level = PressureLevel.OK
                message = f"{disk.letter} 盘空间充足（剩余 {disk.free_gb:.1f} GB）"

            pressures.append(
                DiskPressure(
                    letter=disk.letter,
                    level=level,
                    free_gb=disk.free_gb,
                    used_percent=disk.used_percent,
                    message=message,
                )
            )

        return pressures

    def _attribute_space(self, snapshot: SystemSnapshot) -> list[SpaceAttribution]:
        """将目录占用归因到软件。"""
        attributions: list[SpaceAttribution] = []

        for dir_size in snapshot.top_dirs:
            attr = SpaceAttribution(path=dir_size.path, size_gb=dir_size.size_gb)
            match = self._match_entry_by_path(dir_size.path)
            if match:
                attr.software_id = match.id
                attr.software_name = match.name
                attr.category = match.category.value
            attributions.append(attr)

        return attributions

    def _match_entry_by_path(self, path: str):
        r"""按路径匹配知识库条目。

        匹配策略：
        1. 路径完全相同 → 直接返回
        2. 路径在某个默认路径之下 → 返回最长匹配的条目
        3. 都不匹配 → None

        不允许「默认路径在目录之下」，避免 AppData\Local\Programs
        这种宽泛目录被误归到某个软件。
        """
        normalized = normalize_path(path).lower()
        best_match = None
        best_length = 0

        for entry in self.kb.all():
            candidates = entry.defaultInstallPaths + entry.defaultDataPaths
            for candidate in candidates:
                expanded = normalize_path(candidate).lower()
                if not expanded:
                    continue

                # 精确匹配
                if normalized == expanded:
                    return entry

                # 目录在默认路径之下
                if normalized.startswith(expanded + "\\"):
                    if len(expanded) > best_length:
                        best_match = entry
                        best_length = len(expanded)

        return best_match

    def _find_misplaced(self, snapshot: SystemSnapshot) -> list[MisplacedSoftware]:
        """找出装在非推荐位置的软件。"""
        results: list[MisplacedSoftware] = []
        system_drive = "C:"

        for sw in snapshot.installed:
            if not sw.install_path:
                continue
            if not sw.install_path.upper().startswith(system_drive):
                continue

            entry = self.kb.match_by_name(sw.name)
            if not entry:
                continue

            # 如果推荐路径也在 C 盘，跳过
            if entry.recommendedInstallPath.upper().startswith(system_drive):
                continue

            current = normalize_path(sw.install_path)
            recommended = normalize_path(entry.recommendedInstallPath)

            if current.lower() == recommended.lower():
                continue

            results.append(
                MisplacedSoftware(
                    software_id=entry.id,
                    software_name=entry.name,
                    current_path=sw.install_path,
                    recommended_path=entry.recommendedInstallPath,
                    reason=f"装在 C 盘，推荐迁移到 {entry.recommendedInstallPath}",
                )
            )

        return results

    def _check_env(self, snapshot: SystemSnapshot) -> list[str]:
        """检查环境变量问题。"""
        issues: list[str] = []
        env_map = {ev.name: ev.value for ev in snapshot.env_vars}

        scoop = env_map.get("SCOOP", "")
        if scoop:
            normalized = normalize_path(scoop)
            if normalized.upper().startswith("C:"):
                issues.append(f"SCOOP 指向 C 盘：{scoop}，建议迁移到 D 盘")
        else:
            issues.append("SCOOP 未设置，建议安装 Scoop 并配置到 D 盘")

        return issues