"""磁盘扫描器。"""

from __future__ import annotations

from typing import Any

from diskadvisor.core.models import DiskInfo, DiskType, SystemSnapshot
from diskadvisor.core.utils import run_powershell_json
from diskadvisor.scanner.base import BaseScanner


class DiskScanner(BaseScanner[list[DiskInfo]]):
    """扫描磁盘信息。"""

    name = "disk"

    def scan(self) -> list[DiskInfo]:
        """扫描所有磁盘。"""
        script = """
$volumes = Get-Volume | Where-Object { $_.DriveLetter -ne $null }
$physical = @{}
Get-PhysicalDisk | ForEach-Object {
    $physical[$_.DeviceId] = $_.MediaType
}
$result = $volumes | ForEach-Object {
    [PSCustomObject]@{
        Letter = [string]$_.DriveLetter
        Label = $_.FileSystemLabel
        SizeBytes = [long]$_.Size
        FreeBytes = [long]$_.SizeRemaining
        DriveType = $_.DriveType
    }
}
$result | ConvertTo-Json -Depth 3 -Compress
"""
        raw: Any = run_powershell_json(script, timeout=30)

        if raw is None:
            return []
        if isinstance(raw, dict):
            raw = [raw]

        system_drive = self._get_system_drive()
        disks: list[DiskInfo] = []

        for item in raw:
            letter = item.get("Letter", "").strip()
            if not letter:
                continue

            size_bytes = item.get("SizeBytes") or 0
            free_bytes = item.get("FreeBytes") or 0
            total_gb = round(size_bytes / (1024**3), 2)
            free_gb = round(free_bytes / (1024**3), 2)
            used_percent = round((1 - free_bytes / size_bytes) * 100, 2) if size_bytes > 0 else 0.0

            disk_type = self._guess_disk_type(item.get("DriveType", ""))

            disks.append(
                DiskInfo(
                    letter=letter,
                    total_gb=total_gb,
                    free_gb=free_gb,
                    used_percent=used_percent,
                    disk_type=disk_type,
                    is_system=(letter.upper() == system_drive.upper()),
                    label=item.get("Label") or None,
                )
            )

        disks.sort(key=lambda d: d.letter)
        return disks

    def apply(self, snapshot: SystemSnapshot, result: list[DiskInfo]) -> None:
        snapshot.disks = result

    @staticmethod
    def _get_system_drive() -> str:
        """获取系统盘符。"""
        import os

        return os.environ.get("SystemDrive", "C:").rstrip(":")

    @staticmethod
    def _guess_disk_type(drive_type: str) -> DiskType:
        """根据 DriveType 推断磁盘类型。

        Get-Volume 的 DriveType 取值：Fixed、Removable、Network 等。
        无法直接区分 SSD/HDD，这里先返回 Unknown。
        """
        return DiskType.UNKNOWN