"""执行和回滚 API。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from diskadvisor.analyzer import Analyzer
from diskadvisor.core.config import Settings
from diskadvisor.executor import ExecMode, Executor
from diskadvisor.recommender import Recommender
from diskadvisor.server.deps import collect_snapshot

router = APIRouter()


class ApplyRequest(BaseModel):
    rec_id: str
    mode: str = "dry-run"
    no_deep: bool = False


class ApplyResponse(BaseModel):
    exec_id: str
    success: bool
    operations: list[dict]


@router.post("/apply", response_model=ApplyResponse)
async def do_apply(req: ApplyRequest) -> ApplyResponse:
    """执行推荐。"""
    settings = Settings()
    snapshot = collect_snapshot(settings, no_deep=req.no_deep)
    analysis = Analyzer().analyze(snapshot)
    recs = Recommender().recommend(snapshot, analysis)

    target = next((r for r in recs if r.id == req.rec_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"未找到推荐：{req.rec_id}")

    try:
        mode = ExecMode(req.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效模式：{req.mode}")

    executor = Executor()
    result = executor.execute(target, mode=mode)

    return ApplyResponse(
        exec_id=result.entry.exec_id,
        success=result.success,
        operations=[op.model_dump(mode="json") for op in result.entry.operations],
    )


@router.post("/rollback/{exec_id}")
async def do_rollback(exec_id: str) -> dict:
    """回滚指定会话。"""
    executor = Executor()
    try:
        result = executor.rollback(exec_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "exec_id": exec_id,
        "success": True,
        "operations": [op.model_dump(mode="json") for op in result.entry.operations],
    }