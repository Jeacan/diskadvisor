"""执行日志：记录每次操作，支持回滚。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class OperationType(str, Enum):
    CREATE_DIR = "create_dir"
    SET_ENV_USER = "set_env_user"
    SET_ENV_MACHINE = "set_env_machine"
    RUN_COMMAND = "run_command"


class Operation(BaseModel):
    """单条操作记录。"""

    type: OperationType
    description: str
    # 操作参数
    path: str | None = None
    name: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    command: str | None = None
    # 回滚方式
    rollback: str = ""
    # 执行结果
    success: bool = False
    error: str | None = None


class JournalEntry(BaseModel):
    """一次执行会话的记录。"""

    exec_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
    timestamp: datetime = Field(default_factory=datetime.now)
    rec_id: str = ""
    rec_title: str = ""
    operations: list[Operation] = Field(default_factory=list)
    rolled_back: bool = False


class Journal:
    """执行日志管理器。"""

    def __init__(self, journal_dir: Path | None = None) -> None:
        if journal_dir is None:
            journal_dir = Path.home() / ".diskadvisor" / "journal"
        self.journal_dir = journal_dir
        self.journal_dir.mkdir(parents=True, exist_ok=True)

    def save(self, entry: JournalEntry) -> Path:
        """保存一条日志。"""
        path = self.journal_dir / f"{entry.exec_id}.json"
        path.write_text(
            entry.model_dump_json(indent=2),
            encoding="utf-8",
        )
        return path

    def load(self, exec_id: str) -> JournalEntry | None:
        """加载指定日志。"""
        path = self.journal_dir / f"{exec_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return JournalEntry(**data)

    def list_entries(self) -> list[JournalEntry]:
        """列出所有日志，按时间倒序。"""
        entries: list[JournalEntry] = []
        for path in sorted(self.journal_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                entries.append(JournalEntry(**data))
            except Exception:
                continue
        return entries

    def mark_rolled_back(self, exec_id: str) -> None:
        """标记为已回滚。"""
        entry = self.load(exec_id)
        if entry:
            entry.rolled_back = True
            self.save(entry)