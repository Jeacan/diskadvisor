"""知识库校验器。"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from diskadvisor.kb.models import SoftwareEntry


class ValidationIssue:
    """校验问题。"""

    def __init__(self, file: str, level: str, message: str) -> None:
        self.file = file
        self.level = level  # "error" | "warning"
        self.message = message

    def __str__(self) -> str:
        return f"[{self.level}] {self.file}: {self.message}"


class KBValidator:
    """知识库校验器。"""

    def __init__(self, entries_dir: Path | None = None) -> None:
        if entries_dir is None:
            import sys

            if getattr(sys, "frozen", False):
                base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
                entries_dir = base / "diskadvisor" / "kb" / "entries"
            else:
                entries_dir = Path(__file__).parent / "entries"
        self.entries_dir = entries_dir

    def validate(self) -> list[ValidationIssue]:
        """校验所有条目。"""
        issues: list[ValidationIssue] = []
        seen_ids: dict[str, str] = {}

        if not self.entries_dir.exists():
            issues.append(ValidationIssue(str(self.entries_dir), "error", "目录不存在"))
            return issues

        for json_file in self.entries_dir.rglob("*.json"):
            if json_file.name == "schema.json":
                continue

            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                issues.append(ValidationIssue(json_file.name, "error", f"JSON 解析失败：{e}"))
                continue

            # ID 重复检查
            entry_id = data.get("id", "")
            if entry_id in seen_ids:
                issues.append(
                    ValidationIssue(
                        json_file.name,
                        "error",
                        f"ID 重复：{entry_id}（与 {seen_ids[entry_id]} 冲突）",
                    )
                )
            else:
                seen_ids[entry_id] = json_file.name

            # Schema 校验
            try:
                SoftwareEntry(**data)
            except ValidationError as e:
                issues.append(ValidationIssue(json_file.name, "error", f"Schema 校验失败：{e}"))
                continue

            # 业务规则检查
            issues.extend(self._check_business_rules(json_file.name, data))

        return issues

    def _check_business_rules(self, filename: str, data: dict) -> list[ValidationIssue]:
        """业务规则检查。"""
        issues: list[ValidationIssue] = []

        # 推荐路径建议在 D 盘（Office 除外）
        rec_path = data.get("recommendedInstallPath", "")
        if data.get("id") != "office" and rec_path.upper().startswith("C:"):
            issues.append(
                ValidationIssue(filename, "warning", f"推荐安装路径在 C 盘：{rec_path}")
            )

        # migration 相关字段一致性
        migration = data.get("migration", {})
        if migration.get("data") == "in-app-setting" and not migration.get("steps"):
            issues.append(
                ValidationIssue(filename, "warning", "data=in-app-setting 但没有 migration.steps")
            )

        # scoop 安装方式应该有 command
        for method in data.get("installMethods", []):
            if method.get("method") == "scoop" and not method.get("command"):
                issues.append(
                    ValidationIssue(filename, "warning", "scoop 安装方式缺少 command")
                )

        return issues