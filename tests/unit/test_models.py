"""数据模型测试。"""

from diskadvisor.core.models import DiskInfo, DiskType, SystemSnapshot


def test_disk_info_creation() -> None:
    disk = DiskInfo(
        letter="C",
        total_gb=500.0,
        free_gb=45.0,
        used_percent=91.0,
        disk_type=DiskType.SSD,
        is_system=True,
    )
    assert disk.letter == "C"
    assert disk.used_percent == 91.0


def test_system_snapshot_default() -> None:
    snapshot = SystemSnapshot()
    assert snapshot.disks == []
    assert snapshot.installed == []
    assert snapshot.is_admin is False