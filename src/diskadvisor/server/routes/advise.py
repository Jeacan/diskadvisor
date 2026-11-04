"""单个软件咨询 API。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from diskadvisor.recommender import Recommender

router = APIRouter()


@router.get("/advise/{software}")
async def do_advise(software: str) -> dict:
    """查询单个软件的安装建议。"""
    recommender = Recommender()
    advice = recommender.advise_software(software)

    if not advice:
        raise HTTPException(status_code=404, detail=f"知识库中未找到：{software}")

    return advice.model_dump(mode="json")