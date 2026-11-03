"""冲突检测。"""

from __future__ import annotations

from pathlib import Path

from diskadvisor.recommender.models import Recommendation


class ConflictDetector:
    """检测推荐项之间的冲突。"""

    def detect(self, recs: list[Recommendation]) -> list[Recommendation]:
        """检测冲突并标记。

        冲突类型：
        1. 多个推荐指向同一个目标目录。
        2. 目标目录已存在且非空。

        Returns:
            标记了 conflict 字段的推荐列表。
        """
        path_owners: dict[str, list[Recommendation]] = {}

        for rec in recs:
            for step in rec.steps:
                if step.command and "New-Item" in step.command:
                    target = self._extract_path(step.command)
                    if target:
                        path_owners.setdefault(target.lower(), []).append(rec)

        for path, owners in path_owners.items():
            if len(owners) > 1:
                names = ", ".join(r.id for r in owners)
                for rec in owners:
                    rec.conflict = f"多个推荐使用同一路径 {path}：{names}"

        for rec in recs:
            if rec.conflict:
                continue
            for step in rec.steps:
                if step.command and "New-Item" in step.command:
                    target = self._extract_path(step.command)
                    if target and Path(target).exists():
                        try:
                            if any(Path(target).iterdir()):
                                rec.conflict = f"目标目录已存在且非空：{target}"
                                break
                        except (PermissionError, OSError):
                            continue

        return recs

    @staticmethod
    def _extract_path(command: str) -> str | None:
        """从 New-Item 命令中提取路径。"""
        import re

        match = re.search(r"-Path\s+['\"]([^'\"]+)['\"]", command)
        if match:
            return match.group(1)
        return None