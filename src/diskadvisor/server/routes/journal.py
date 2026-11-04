"""执行日志 API。"""

from __future__ import annotations

from fastapi import APIRouter, Query

from diskadvisor.executor import Journal

router = APIRouter()


@router.get("/journal")
async def list_journal(limit: int = Query(20)) -> list[dict]:
    """列出执行日志。"""
    journal = Journal()
    entries = journal.list_entries()[:limit]
    return [e.model_dump(mode="json") for e in entries]


@router.get("/journal/{exec_id}")
async def get_journal(exec_id: str) -> dict:
    """获取指定日志详情。"""
    journal = Journal()
    entry = journal.load(exec_id)
    if not entry:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"未找到：{exec_id}")
    return entry.model_dump(mode="json")