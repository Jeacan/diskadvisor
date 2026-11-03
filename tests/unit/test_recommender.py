"""推荐引擎测试。"""

from diskadvisor.analyzer.models import (
    AnalysisResult,
    MisplacedSoftware,
    PressureLevel,
    DiskPressure,
)
from diskadvisor.core.models import DiskInfo, DiskType, SystemSnapshot
from diskadvisor.recommender import Recommender


def test_advise_wechat() -> None:
    recommender = Recommender()
    advice = recommender.advise_software("wechat")
    assert advice is not None
    assert advice.software_id == "wechat"
    assert "D:" in advice.recommended_install_path


def test_advise_unknown_returns_none() -> None:
    recommender = Recommender()
    advice = recommender.advise_software("nonexistent-software-xyz")
    assert advice is None


def test_recommend_for_misplaced() -> None:
    snapshot = SystemSnapshot()
    analysis = AnalysisResult(
        misplaced=[
            MisplacedSoftware(
                software_id="wechat",
                software_name="微信",
                current_path="C:\\Program Files\\Tencent\\WeChat",
                recommended_path="D:\\SocialApps\\WeChat",
                reason="装在 C 盘",
            )
        ]
    )
    recommender = Recommender()
    recs = recommender.recommend(snapshot, analysis)
    assert len(recs) >= 1
    assert any(r.kb_ref == "wechat" for r in recs)


def test_recommend_emergency_boost() -> None:
    snapshot = SystemSnapshot()
    analysis = AnalysisResult(
        disk_pressures=[
            DiskPressure(
                letter="C",
                level=PressureLevel.CRITICAL,
                free_gb=5.0,
                used_percent=99.0,
                message="C 盘空间严重不足",
            )
        ],
        env_issues=["SCOOP 未设置，建议安装 Scoop 并配置到 D 盘"],
    )
    recommender = Recommender()
    recs = recommender.recommend(snapshot, analysis)
    assert any(r.id == "config-scoop" for r in recs)