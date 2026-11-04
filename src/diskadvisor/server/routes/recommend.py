"""推荐 API。"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from diskadvisor.analyzer import Analyzer
from diskadvisor.core.config import Settings
from diskadvisor.executor import ScriptGenerator
from diskadvisor.recommender import Recommender
from diskadvisor.reporter import render_recommendations
from diskadvisor.server.deps import collect_snapshot

router = APIRouter()


class RecommendResponse(BaseModel):
    recommendations: list[dict]
    report_markdown: str
    script: str


@router.post("/recommend", response_model=RecommendResponse)
async def do_recommend(
    no_deep: bool = Query(False),
    top: int = Query(20, description="最多返回条数"),
    include_manual: bool = Query(False),
    force_refresh: bool = Query(False, description="强制刷新缓存"),
) -> RecommendResponse:
    """生成推荐列表和脚本。"""
    settings = Settings()
    snapshot = collect_snapshot(settings, no_deep=no_deep, force_refresh=force_refresh)

    analyzer = Analyzer()
    analysis = analyzer.analyze(snapshot)

    recommender = Recommender()
    recs = recommender.recommend(snapshot, analysis)

    if top > 0:
        recs = recs[:top]

    report = render_recommendations(recs)
    gen = ScriptGenerator()
    script = gen.generate(recs, include_manual=include_manual)

    return RecommendResponse(
        recommendations=[r.model_dump(mode="json") for r in recs],
        report_markdown=report,
        script=script,
    )