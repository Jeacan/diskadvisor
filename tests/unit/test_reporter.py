"""报告生成器测试。"""

from diskadvisor.core.models import DiskInfo, DiskType, SystemSnapshot
from diskadvisor.reporter import render_diagnosis


def test_render_diagnosis_contains_disk_table() -> None:
    snapshot = SystemSnapshot(
        disks=[
            DiskInfo(
                letter="C",
                total_gb=500.0,
                free_gb=45.0,
                used_percent=91.0,
                disk_type=DiskType.SSD,
                is_system=True,
            )
        ]
    )
    report = render_diagnosis(snapshot)
    assert "# DiskAdvisor 诊断报告" in report
    assert "| C |" in report
    assert "🔴 紧张" in report


def test_render_diagnosis_empty() -> None:
    snapshot = SystemSnapshot()
    report = render_diagnosis(snapshot)
    assert "未采集到磁盘信息" in report