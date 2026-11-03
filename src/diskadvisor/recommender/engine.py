"""推荐引擎。"""

from __future__ import annotations

from loguru import logger

from diskadvisor.analyzer.models import AnalysisResult, PressureLevel
from diskadvisor.core.models import SystemSnapshot
from diskadvisor.core.utils.paths import normalize_path
from diskadvisor.kb import KnowledgeBase, SoftwareEntry
from diskadvisor.recommender.conflict import ConflictDetector
from diskadvisor.recommender.models import (
    Difficulty,
    InstallationAdvice,
    RecCategory,
    Recommendation,
    Risk,
    Step,
)
from diskadvisor.recommender.scorer import Scorer


class Recommender:
    """生成推荐。"""

    def __init__(self, kb: KnowledgeBase | None = None) -> None:
        self.kb = kb or KnowledgeBase()
        self.scorer = Scorer()
        self.conflict_detector = ConflictDetector()

    def recommend(
        self,
        snapshot: SystemSnapshot,
        analysis: AnalysisResult,
    ) -> list[Recommendation]:
        """生成推荐列表。

        Args:
            snapshot: 系统快照。
            analysis: 分析结果。

        Returns:
            排序后的推荐列表。
        """
        recs: list[Recommendation] = []

        recs.extend(self._recs_for_misplaced(analysis))
        recs.extend(self._recs_for_env(analysis))
        recs.extend(self._recs_for_big_dirs(snapshot, analysis))

        boost = self._emergency_boost(analysis)
        recs = self.scorer.rank(recs, priority_boost=boost)
        recs = self.conflict_detector.detect(recs)

        return recs

    def advise_software(self, software_name: str) -> InstallationAdvice | None:
        """为单个软件生成安装建议。

        Args:
            software_name: 软件名或 ID。

        Returns:
            安装建议；未找到返回 None。
        """
        entry = self.kb.get(software_name) or self.kb.match_by_name(software_name)
        if not entry:
            logger.debug("知识库中未找到：{}", software_name)
            return None

        return self._entry_to_advice(entry)

    def _recs_for_misplaced(self, analysis: AnalysisResult) -> list[Recommendation]:
        """为装在 C 盘的软件生成迁移推荐。"""
        recs: list[Recommendation] = []

        for m in analysis.misplaced:
            entry = self.kb.get(m.software_id)
            if not entry:
                continue

            steps: list[Step] = []
            if entry.migration.auto_migratable and entry.installMethods:
                method = entry.installMethods[0]
                if method.method.value == "scoop" and method.command:
                    steps.append(
                        Step(
                            order=1,
                            description=f"使用 Scoop 安装 {entry.name}",
                            command=method.command,
                            manual=False,
                        )
                    )
                else:
                    steps.append(
                        Step(
                            order=1,
                            description=f"卸载 {entry.name}",
                            command=None,
                            manual=True,
                        )
                    )
            else:
                for i, s in enumerate(entry.migration.steps, start=1):
                    steps.append(Step(order=i, description=s, manual=True))

            risk = Risk(entry.migration.risk.value)
            recs.append(
                Recommendation(
                    id=f"migrate-{entry.id}",
                    category=RecCategory.MIGRATE,
                    title=f"迁移 {entry.name} 到 D 盘",
                    reason=m.reason,
                    impact_gb=0.0,
                    difficulty=Difficulty.EASY if entry.migration.auto_migratable else Difficulty.MEDIUM,
                    risk=risk,
                    steps=steps,
                    auto_executable=entry.migration.auto_migratable,
                    estimated_minutes=5 if entry.migration.auto_migratable else 15,
                    kb_ref=entry.id,
                )
            )

        return recs

    def _recs_for_env(self, analysis: AnalysisResult) -> list[Recommendation]:
        """为环境变量问题生成推荐。"""
        recs: list[Recommendation] = []

        for issue in analysis.env_issues:
            if "SCOOP" not in issue:
                continue

            if "未设置" in issue:
                steps = [
                    Step(
                        order=1,
                        description="设置 SCOOP 环境变量到 D 盘",
                        command='[Environment]::SetEnvironmentVariable("SCOOP", "D:\\Developer\\Scoop", "User")',
                        manual=False,
                    ),
                    Step(
                        order=2,
                        description="安装 Scoop",
                        command="irm get.scoop.sh | iex",
                        manual=False,
                        warning="需要在普通 PowerShell（非管理员）中执行",
                    ),
                ]
                title = "配置 Scoop 到 D 盘"
                reason = "Scoop 未配置，开发工具建议统一通过 Scoop 管理"
            else:
                steps = [
                    Step(
                        order=1,
                        description="备份当前 Scoop 目录",
                        command=None,
                        manual=True,
                    ),
                    Step(
                        order=2,
                        description="迁移 Scoop 目录到 D:\\Developer\\Scoop",
                        command=None,
                        manual=True,
                    ),
                    Step(
                        order=3,
                        description="更新 SCOOP 环境变量",
                        command='[Environment]::SetEnvironmentVariable("SCOOP", "D:\\Developer\\Scoop", "User")',
                        manual=False,
                    ),
                ]
                title = "迁移 Scoop 到 D 盘"
                reason = issue

            recs.append(
                Recommendation(
                    id="config-scoop",
                    category=RecCategory.ENV,
                    title=title,
                    reason=reason,
                    impact_gb=0.0,
                    difficulty=Difficulty.EASY,
                    risk=Risk.LOW,
                    steps=steps,
                    auto_executable=False,
                    estimated_minutes=5,
                )
            )

        return recs

    def _recs_for_big_dirs(
        self,
        snapshot: SystemSnapshot,
        analysis: AnalysisResult,
    ) -> list[Recommendation]:
        """为大的 C 盘目录生成推荐。"""
        recs: list[Recommendation] = []

        for attr in analysis.attributions:
            if not attr.software_id or attr.size_gb < 1.0:
                continue
            if not attr.path.upper().startswith("C:"):
                continue

            entry = self.kb.get(attr.software_id)
            if not entry:
                continue
            # 官方不建议迁移的条目跳过
            if entry.migration.install == "none" and entry.migration.data == "none":
                continue
            if not entry.migration.steps:
                continue

            steps = [
                Step(order=i, description=s, manual=True)
                for i, s in enumerate(entry.migration.steps, start=1)
            ]
            recs.append(
                Recommendation(
                    id=f"migrate-dir-{entry.id}",
                    category=RecCategory.MIGRATE,
                    title=f"迁移 {entry.name} 数据目录（{attr.size_gb:.1f} GB）",
                    reason=f"{attr.path} 占用 {attr.size_gb:.1f} GB",
                    impact_gb=attr.size_gb,
                    difficulty=Difficulty.MEDIUM,
                    risk=Risk(entry.migration.risk.value),
                    steps=steps,
                    auto_executable=False,
                    estimated_minutes=10,
                    kb_ref=entry.id,
                )
            )

        return recs

    @staticmethod
    def _emergency_boost(analysis: AnalysisResult) -> float:
        """C 盘紧急时给迁移类推荐加成。"""
        for p in analysis.disk_pressures:
            if p.letter.upper() == "C" and p.level == PressureLevel.CRITICAL:
                return 10.0
        return 0.0

    @staticmethod
    def _entry_to_advice(entry: SoftwareEntry) -> InstallationAdvice:
        """把知识库条目转成安装建议。"""
        method = entry.installMethods[0] if entry.installMethods else None
        version_mgmt = None
        if entry.versionManagement:
            version_mgmt = {
                "tool": entry.versionManagement.tool,
                "method": entry.versionManagement.method,
                "commands": entry.versionManagement.commands,
            }

        return InstallationAdvice(
            software_id=entry.id,
            software_name=entry.name,
            recommended_install_path=entry.recommendedInstallPath,
            recommended_data_path=entry.recommendedDataPath,
            install_method=method.method.value if method else None,
            install_command=method.command if method else None,
            env_vars=[v.model_dump() for v in entry.envVars],
            version_management=version_mgmt,
            migration_steps=entry.migration.steps,
            notes=entry.notes,
        )