"""扫描 API。"""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from diskadvisor.analyzer import Analyzer
from diskadvisor.core.config import Settings
from diskadvisor.reporter import render_diagnosis
from diskadvisor.server.cache import get_cache, make_key
from diskadvisor.server.deps import collect_snapshot

router = APIRouter()


class ScanResponse(BaseModel):
    snapshot: dict
    analysis: dict
    report_markdown: str
    elapsed_seconds: float
    from_cache: bool


@router.post("/scan", response_model=ScanResponse)
async def do_scan(
    no_deep: bool = Query(False, description="跳过目录和大文件扫描"),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
) -> ScanResponse:
    """扫描系统并返回诊断结果。"""
    settings = Settings()
    cache = get_cache()
    key = make_key(settings, no_deep)

    # 判断是否命中缓存（在 collect 之前查，因为 collect 之后缓存已被填充）
    from_cache = False
    if not force_refresh and cache.get(key) is not None:
        from_cache = True

    start = time.time()
    snapshot = collect_snapshot(
        settings,
        no_deep=no_deep,
        force_refresh=force_refresh,
    )
    analysis = Analyzer().analyze(snapshot)
    elapsed = time.time() - start

    report = render_diagnosis(snapshot, analysis)

    return ScanResponse(
        snapshot=snapshot.model_dump(mode="json"),
        analysis=analysis.model_dump(mode="json"),
        report_markdown=report,
        elapsed_seconds=round(elapsed, 2),
        from_cache=from_cache,
    )


@router.post("/scan/async")
async def do_scan_async(
    no_deep: bool = Query(False),
    force_refresh: bool = Query(False),
) -> dict:
    """创建后台扫描任务（可选，用于超长扫描）。"""
    from diskadvisor.server.tasks import create_scan_task

    task_id = create_scan_task(no_deep, force_refresh)
    return {"task_id": task_id}


@router.get("/scan/task/{task_id}")
async def get_scan_task(task_id: str) -> dict:
    """查询扫描任务状态。"""
    from diskadvisor.server.tasks import get_task

    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "id": task.id,
        "status": task.status.value,
        "stage": task.stage,
        "result": task.result,
        "error": task.error,
    }


@router.post("/cache/clear")
async def clear_cache() -> dict:
    """清空扫描缓存。"""
    get_cache().clear()
    return {"ok": True}

@router.post("/scan/async")
async def do_scan_async(
    no_deep: bool = Query(False),
    force_refresh: bool = Query(False),
) -> dict:
    """创建后台扫描任务。"""
    from diskadvisor.server.tasks import create_scan_task

    task_id = create_scan_task(no_deep, force_refresh)
    return {"task_id": task_id}


@router.get("/scan/task/{task_id}")
async def get_scan_task(task_id: str) -> dict:
    """查询扫描任务状态。"""
    from diskadvisor.server.tasks import get_task

    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "id": task.id,
        "status": task.status.value,
        "stage": task.stage,
        "result": task.result,
        "error": task.error,
    }