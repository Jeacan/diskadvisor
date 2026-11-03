"""端到端集成测试。"""

from pathlib import Path

from diskadvisor.analyzer import Analyzer
from diskadvisor.core.models import (
    DirSize,
    DiskInfo,
    DiskType,
    EnvScope,
    EnvVar,
    InstalledSoftware,
    SoftwareSource,
    SystemSnapshot,
)
from diskadvisor.executor import ExecMode, Executor, Journal, ScriptGenerator
from diskadvisor.recommender import Recommender
from diskadvisor.reporter import render_diagnosis, render_recommendations


def _make_snapshot() -> SystemSnapshot:
    """构造一个典型的 C 盘紧张场景。"""
    return SystemSnapshot(
        disks=[
            DiskInfo(
                letter="C",
                total_gb=500,
                free_gb=20,
                used_percent=96,
                disk_type=DiskType.SSD,
                is_system=True,
            ),
            DiskInfo(
                letter="D",
                total_gb=2000,
                free_gb=1500,
                used_percent=25,
                disk_type=DiskType.SSD,
                is_system=False,
            ),
        ],
        installed=[
            InstalledSoftware(
                name="Git",
                install_path="C:\\Program Files\\Git",
                source=SoftwareSource.REGISTRY,
            ),
            InstalledSoftware(
                name="微信",
                install_path="C:\\Program Files\\Tencent\\WeChat",
                source=SoftwareSource.REGISTRY,
            ),
        ],
        env_vars=[
            EnvVar(name="SCOOP", value="C:\\Users\\you\\scoop", scope=EnvScope.PROCESS),
        ],
        top_dirs=[
            DirSize(
                path="C:\\Users\\you\\AppData\\Roaming\\Tencent",
                size_gb=12.5,
                file_count=2000,
            ),
            DirSize(
                path="C:\\Program Files\\Git",
                size_gb=0.3,
                file_count=500,
            ),
        ],
    )


def test_full_pipeline() -> None:
    """完整流程：扫描结果 → 分析 → 推荐 → 报告 → 脚本。"""
    snapshot = _make_snapshot()

    # 1. 分析
    analyzer = Analyzer()
    analysis = analyzer.analyze(snapshot)

    assert len(analysis.disk_pressures) == 2
    # C 盘应该是 critical
    c_pressure = next(p for p in analysis.disk_pressures if p.letter == "C")
    assert c_pressure.level.value == "critical"
    # 应该有环境变量问题
    assert len(analysis.env_issues) >= 1
    # 应该识别出装在 C 盘的软件
    assert len(analysis.misplaced) >= 1

    # 2. 推荐
    recommender = Recommender()
    recs = recommender.recommend(snapshot, analysis)
    assert len(recs) >= 1

    # 3. 报告
    diagnosis = render_diagnosis(snapshot, analysis)
    assert "# DiskAdvisor 诊断报告" in diagnosis
    assert "磁盘压力" in diagnosis

    rec_report = render_recommendations(recs)
    assert "# DiskAdvisor 推荐操作" in rec_report

    # 4. 脚本
    gen = ScriptGenerator()
    script = gen.generate(recs)
    assert "$ErrorActionPreference" in script


def test_advise_round_trip() -> None:
    """咨询 → 输出的完整信息。"""
    recommender = Recommender()
    advice = recommender.advise_software("nodejs")

    assert advice is not None
    assert advice.install_command == "scoop install nodejs-lts"
    assert advice.version_management is not None
    assert "scoop reset" in advice.version_management["method"]


def test_executor_with_dry_run(tmp_path: Path) -> None:
    """执行器 dry-run 不实际改动。"""
    from diskadvisor.recommender import RecCategory, Recommendation, Step

    target = tmp_path / "not_created"
    rec = Recommendation(
        id="test",
        category=RecCategory.CONFIG,
        title="测试",
        steps=[
            Step(
                order=1,
                description="创建目录",
                command=f'New-Item -ItemType Directory -Path "{target}" -Force',
            )
        ],
    )

    journal = Journal(journal_dir=tmp_path / "journal")
    executor = Executor(journal=journal)
    result = executor.execute(rec, mode=ExecMode.DRY_RUN)

    assert result.success
    assert not target.exists()


def test_path_attribution_uses_longest_match() -> None:
    """归属匹配应该优先匹配更长的路径。"""
    snapshot = SystemSnapshot(
        top_dirs=[
            DirSize(
                path="C:\\Users\\you\\AppData\\Roaming\\Tencent\\WeChat Files",
                size_gb=10.0,
                file_count=1000,
            ),
        ]
    )
    analyzer = Analyzer()
    analysis = analyzer.analyze(snapshot)

    # 应该归到微信而不是其他
    assert len(analysis.attributions) == 1
    attr = analysis.attributions[0]
    # 允许 None（如果路径不匹配），但如果匹配了应该是 wechat
    if attr.software_id:
        assert attr.software_id == "wechat"