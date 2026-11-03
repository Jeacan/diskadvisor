"""分析器测试。"""

from diskadvisor.analyzer import Analyzer, PressureLevel
from diskadvisor.core.models import DiskInfo, DiskType, DirSize, SystemSnapshot


def test_disk_pressure_critical() -> None:
    snapshot = SystemSnapshot(
        disks=[
            DiskInfo(
                letter="C",
                total_gb=500,
                free_gb=20,
                used_percent=96,
                disk_type=DiskType.SSD,
                is_system=True,
            )
        ]
    )
    analyzer = Analyzer()
    result = analyzer.analyze(snapshot)
    assert len(result.disk_pressures) == 1
    assert result.disk_pressures[0].level == PressureLevel.CRITICAL


def test_disk_pressure_ok() -> None:
    snapshot = SystemSnapshot(
        disks=[
            DiskInfo(
                letter="D",
                total_gb=2000,
                free_gb=1500,
                used_percent=25,
                disk_type=DiskType.SSD,
                is_system=False,
            )
        ]
    )
    analyzer = Analyzer()
    result = analyzer.analyze(snapshot)
    assert result.disk_pressures[0].level == PressureLevel.OK


def test_env_issue_scoop_c_drive() -> None:
    from diskadvisor.core.models import EnvScope, EnvVar

    snapshot = SystemSnapshot(
        env_vars=[
            EnvVar(name="SCOOP", value="C:\\Users\\you\\scoop", scope=EnvScope.PROCESS)
        ]
    )
    analyzer = Analyzer()
    result = analyzer.analyze(snapshot)
    assert any("SCOOP" in issue for issue in result.env_issues)