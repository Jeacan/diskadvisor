"""推荐评分器。"""

from __future__ import annotations

from diskadvisor.recommender.models import (
    Difficulty,
    Priority,
    Recommendation,
    Risk,
)

DIFFICULTY_WEIGHT = {
    Difficulty.EASY: 5.0,
    Difficulty.MEDIUM: 2.0,
    Difficulty.HARD: 0.0,
}

RISK_WEIGHT = {
    Risk.LOW: 5.0,
    Risk.MEDIUM: 2.0,
    Risk.HIGH: -5.0,
}

CATEGORY_WEIGHT = {
    "migrate": 3.0,
    "install": 2.0,
    "env": 2.5,
    "config": 1.5,
}


class Scorer:
    """为推荐项打分并排序。"""

    def score(self, rec: Recommendation, priority_boost: float = 0.0) -> float:
        """计算单条推荐分数。

        Args:
            rec: 推荐项。
            priority_boost: 额外加成（如 C 盘紧急模式）。

        Returns:
            分数，越高越优先。
        """
        impact = rec.impact_gb * 1.0
        difficulty = DIFFICULTY_WEIGHT.get(rec.difficulty, 0.0) * 2.0
        risk = RISK_WEIGHT.get(rec.risk, 0.0) * 3.0
        category = CATEGORY_WEIGHT.get(rec.category.value, 0.0)

        total = impact + difficulty + risk + category + priority_boost
        return round(total, 2)

    def apply_priority(self, score: float) -> Priority:
        """根据分数推导优先级。"""
        if score >= 30:
            return Priority.CRITICAL
        if score >= 15:
            return Priority.HIGH
        if score >= 5:
            return Priority.MEDIUM
        return Priority.LOW

    def rank(
        self,
        recs: list[Recommendation],
        priority_boost: float = 0.0,
    ) -> list[Recommendation]:
        """为所有推荐打分、更新优先级并排序。"""
        for rec in recs:
            rec.score = self.score(rec, priority_boost=priority_boost)
            rec.priority = self.apply_priority(rec.score)

        return sorted(recs, key=lambda r: r.score, reverse=True)