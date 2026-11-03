"""知识库加载器。"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from diskadvisor.kb.models import SoftwareEntry


class KnowledgeBaseError(RuntimeError):
    """知识库错误。"""


class KnowledgeBase:
    """软件知识库。"""

    def __init__(self, entries_dir: Path | None = None) -> None:
        if entries_dir is None:
            import sys

            if getattr(sys, "frozen", False):
                base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
                entries_dir = base / "diskadvisor" / "kb" / "entries"
            else:
                entries_dir = Path(__file__).parent / "entries"
        self.entries_dir = entries_dir
        self._entries: dict[str, SoftwareEntry] = {}
        self._loaded = False

    def load(self) -> None:
        """加载所有条目。"""
        if self._loaded:
            return

        if not self.entries_dir.exists():
            raise KnowledgeBaseError(f"知识库目录不存在：{self.entries_dir}")

        errors: list[str] = []
        count = 0

        for json_file in self.entries_dir.rglob("*.json"):
            if json_file.name == "schema.json":
                continue
            try:
                entry = self._load_entry(json_file)
                self._entries[entry.id] = entry
                count += 1
            except Exception as e:
                errors.append(f"{json_file.name}: {e}")
                logger.warning("加载知识库条目失败：{} - {}", json_file, e)

        self._loaded = True
        logger.info("知识库加载完成：{} 个条目", count)

        if errors:
            logger.warning("有 {} 个条目加载失败", len(errors))

    def _load_entry(self, path: Path) -> SoftwareEntry:
        """加载单个条目。"""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise KnowledgeBaseError(f"JSON 解析失败：{e}") from e

        try:
            return SoftwareEntry(**data)
        except ValidationError as e:
            raise KnowledgeBaseError(f"Schema 校验失败：{e}") from e

    def get(self, software_id: str) -> SoftwareEntry | None:
        """按 ID 获取条目。"""
        self.load()
        return self._entries.get(software_id)

    def all(self) -> list[SoftwareEntry]:
        """获取所有条目。"""
        self.load()
        return list(self._entries.values())

    def search(self, keyword: str) -> list[SoftwareEntry]:
        """按关键词搜索。

        匹配 id、name、aliases。
        """
        self.load()
        keyword_lower = keyword.lower()
        results: list[SoftwareEntry] = []

        for entry in self._entries.values():
            if (
                keyword_lower in entry.id.lower()
                or keyword_lower in entry.name.lower()
                or any(keyword_lower in alias.lower() for alias in entry.aliases)
            ):
                results.append(entry)

        return results

    def match_by_name(self, name: str) -> SoftwareEntry | None:
        """按软件名精确匹配（不区分大小写）。"""
        self.load()
        name_lower = name.lower()
        for entry in self._entries.values():
            if entry.name.lower() == name_lower:
                return entry
            if any(alias.lower() == name_lower for alias in entry.aliases):
                return entry
        return None