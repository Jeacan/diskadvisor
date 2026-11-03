"""评分器测试。"""

from diskadvisor.recommender import Difficulty, Priority, RecCategory, Recommendation, Risk
from diskadvisor.recommender.scorer import Scorer


def test_score_easy_low_risk_big_impact() -> None:
    rec = Recommendation(
        id="test",
        category=RecCategory.MIGRATE,
        title="测试",
        impact_gb=20.0,
        difficulty=Difficulty.EASY,
        risk=Risk.LOW,
    )
    scorer = Scorer()
    score = scorer.score(rec)
    assert score >= 30
    assert scorer.apply_priority(score) == Priority.CRITICAL


def test_score_hard_high_risk() -> None:
    rec = Recommendation(
        id="test",
        category=RecCategory.CONFIG,
        title="测试",
        impact_gb=1.0,
        difficulty=Difficulty.HARD,
        risk=Risk.HIGH,
    )
    scorer = Scorer()
    score = scorer.score(rec)
    assert score < 0


def test_rank_orders_by_score() -> None:
    big = Recommendation(
        id="big",
        category=RecCategory.MIGRATE,
        title="大",
        impact_gb=50.0,
        difficulty=Difficulty.EASY,
        risk=Risk.LOW,
    )
    small = Recommendation(
        id="small",
        category=RecCategory.CONFIG,
        title="小",
        impact_gb=0.0,
        difficulty=Difficulty.HARD,
        risk=Risk.MEDIUM,
    )
    scorer = Scorer()
    ranked = scorer.rank([small, big])
    assert ranked[0].id == "big"