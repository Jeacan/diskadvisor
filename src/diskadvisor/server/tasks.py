"""后台扫描任务。"""

from __future__ import annotations

import threading
import time
import uuid
from enum import Enum

from diskadvisor.analyzer import Analyzer
from diskadvisor.core.config import Settings
from diskadvisor.reporter import render_diagnosis
from diskadvisor.server.deps import collect_snapshot


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Task:
    def __init__(self) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.status = TaskStatus.PENDING
        self.stage = "排队中"
        self.result: dict | None = None
        self.error: str | None = None
        self.created_at = time.time()


_tasks: dict[str, Task] = {}
_lock = threading.Lock()


def create_scan_task(no_deep: bool, force_refresh: bool) -> str:
    """创建后台扫描任务，返回 task_id。"""
    task = Task()
    with _lock:
        _tasks[task.id] = task

    def _run() -> None:
        try:
            task.status = TaskStatus.RUNNING
            task.stage = "扫描磁盘"
            settings = Settings()
            snapshot = collect_snapshot(settings, no_deep=no_deep, force_refresh=force_refresh)

            task.stage = "分析"
            analysis = Analyzer().analyze(snapshot)
            report = render_diagnosis(snapshot, analysis)

            task.result = {
                "snapshot": snapshot.model_dump(mode="json"),
                "analysis": analysis.model_dump(mode="json"),
                "report_markdown": report,
            }
            task.stage = "完成"
            task.status = TaskStatus.DONE
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

    threading.Thread(target=_run, daemon=True).start()
    return task.id


def get_task(task_id: str) -> Task | None:
    with _lock:
        return _tasks.get(task_id)


def cleanup_old_tasks(max_age_seconds: int = 3600) -> None:
    """清理 1 小时前的任务。"""
    now = time.time()
    with _lock:
        expired = [k for k, v in _tasks.items() if now - v.created_at > max_age_seconds]
        for k in expired:
            del _tasks[k]