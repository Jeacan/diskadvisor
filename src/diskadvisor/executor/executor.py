"""执行器：把推荐转成实际操作。"""

from __future__ import annotations

import os
import subprocess
from enum import Enum
from pathlib import Path

from loguru import logger

from diskadvisor.executor.journal import (
    Journal,
    JournalEntry,
    Operation,
    OperationType,
)
from diskadvisor.recommender.models import Recommendation, Step


class ExecMode(str, Enum):
    DRY_RUN = "dry-run"
    INTERACTIVE = "interactive"
    AUTO = "auto"


class ExecResult:
    """执行结果。"""

    def __init__(self, entry: JournalEntry) -> None:
        self.entry = entry

    @property
    def success(self) -> bool:
        return all(op.success for op in self.entry.operations)

    @property
    def failed_ops(self) -> list[Operation]:
        return [op for op in self.entry.operations if not op.success]


class Executor:
    """执行推荐项。"""

    def __init__(self, journal: Journal | None = None) -> None:
        self.journal = journal or Journal()

    def execute(
        self,
        rec: Recommendation,
        mode: ExecMode = ExecMode.DRY_RUN,
    ) -> ExecResult:
        """执行单条推荐。

        Args:
            rec: 推荐项。
            mode: 执行模式。

        Returns:
            执行结果。
        """
        entry = JournalEntry(rec_id=rec.id, rec_title=rec.title)

        if rec.conflict:
            logger.warning("推荐存在冲突，跳过：{}", rec.conflict)
            return ExecResult(entry)

        for step in rec.steps:
            op = self._step_to_operation(step)
            if not op:
                continue

            if mode == ExecMode.DRY_RUN:
                op.success = True
                op.error = "[dry-run] 未执行"
                entry.operations.append(op)
                continue

            if mode == ExecMode.INTERACTIVE:
                # 交互模式由 CLI 层确认，这里直接执行
                pass

            self._apply(op)
            entry.operations.append(op)

            if not op.success and mode == ExecMode.INTERACTIVE:
                logger.error("步骤失败，停止执行：{}", op.error)
                break

        self.journal.save(entry)
        return ExecResult(entry)

    def rollback(self, exec_id: str) -> ExecResult:
        """回滚指定会话。"""
        entry = self.journal.load(exec_id)
        if not entry:
            raise ValueError(f"未找到执行记录：{exec_id}")
        if entry.rolled_back:
            raise ValueError(f"已回滚过：{exec_id}")

        for op in reversed(entry.operations):
            if not op.success:
                continue
            self._rollback_op(op)

        self.journal.mark_rolled_back(exec_id)
        return ExecResult(entry)

    def _step_to_operation(self, step: Step) -> Operation | None:
        """把步骤转成可执行操作。"""
        if not step.command:
            return None

        cmd = step.command

        # 创建目录
        if "New-Item" in cmd and "Directory" in cmd:
            path = self._extract_path(cmd)
            if path:
                return Operation(
                    type=OperationType.CREATE_DIR,
                    description=step.description,
                    path=path,
                    command=cmd,
                    rollback="remove_dir_if_empty",
                )

        # 设置用户环境变量
        if "SetEnvironmentVariable" in cmd and '"User"' in cmd:
            name, value = self._extract_env(cmd)
            if name:
                old = os.environ.get(name)
                return Operation(
                    type=OperationType.SET_ENV_USER,
                    description=step.description,
                    name=name,
                    old_value=old,
                    new_value=value,
                    command=cmd,
                    rollback="restore_env",
                )

        # 其他命令
        return Operation(
            type=OperationType.RUN_COMMAND,
            description=step.description,
            command=cmd,
            rollback="none",
        )

    def _apply(self, op: Operation) -> None:
        """执行操作。"""
        try:
            if op.type == OperationType.CREATE_DIR:
                assert op.path
                Path(op.path).mkdir(parents=True, exist_ok=True)
                op.success = True
                logger.info("创建目录：{}", op.path)

            elif op.type in (OperationType.SET_ENV_USER, OperationType.SET_ENV_MACHINE):
                assert op.name
                scope = "User" if op.type == OperationType.SET_ENV_USER else "Machine"
                script = (
                    f'[Environment]::SetEnvironmentVariable('
                    f'"{op.name}", "{op.new_value}", "{scope}")'
                )
                self._run_ps(script)
                op.success = True
                logger.info("设置环境变量：{}={}", op.name, op.new_value)

            elif op.type == OperationType.RUN_COMMAND:
                assert op.command
                self._run_ps(op.command)
                op.success = True
                logger.info("执行命令：{}", op.command[:80])

        except Exception as e:
            op.success = False
            op.error = str(e)
            logger.error("操作失败：{} - {}", op.description, e)

    def _rollback_op(self, op: Operation) -> None:
        """回滚单个操作。"""
        try:
            if op.rollback == "remove_dir_if_empty" and op.path:
                p = Path(op.path)
                if p.exists() and not any(p.iterdir()):
                    p.rmdir()
                    logger.info("回滚：删除空目录 {}", op.path)

            elif op.rollback == "restore_env" and op.name:
                script = (
                    f'[Environment]::SetEnvironmentVariable('
                    f'"{op.name}", "{op.old_value or ""}", "User")'
                )
                self._run_ps(script)
                logger.info("回滚：恢复环境变量 {}", op.name)

        except Exception as e:
            logger.warning("回滚失败：{} - {}", op.description, e)

    @staticmethod
    def _run_ps(script: str) -> None:
        """执行 PowerShell 脚本。"""
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

    @staticmethod
    def _extract_path(cmd: str) -> str | None:
        import re

        match = re.search(r"-Path\s+['\"]([^'\"]+)['\"]", cmd)
        return match.group(1) if match else None

    @staticmethod
    def _extract_env(cmd: str) -> tuple[str | None, str | None]:
        import re

        match = re.search(
            r'SetEnvironmentVariable\(\s*"([^"]+)"\s*,\s*"([^"]*)"',
            cmd,
        )
        if match:
            return match.group(1), match.group(2)
        return None, None