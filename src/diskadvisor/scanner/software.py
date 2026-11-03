"""软件扫描器。"""

from __future__ import annotations

from typing import Any

from loguru import logger

from diskadvisor.core.models import InstalledSoftware, SoftwareSource, SystemSnapshot
from diskadvisor.core.utils import run_powershell_json
from diskadvisor.scanner.base import BaseScanner


class SoftwareScanner(BaseScanner[list[InstalledSoftware]]):
    """扫描已安装软件。

    数据来源：
    1. 注册表 Uninstall 键（传统安装）
    2. scoop list
    3. winget list
    """

    name = "software"

    def scan(self) -> list[InstalledSoftware]:
        """扫描已安装软件。"""
        result: list[InstalledSoftware] = []
        result.extend(self._scan_registry())
        result.extend(self._scan_scoop())
        result.extend(self._scan_winget())
        return result

    def apply(self, snapshot: SystemSnapshot, result: list[InstalledSoftware]) -> None:
        snapshot.installed = result

    def _scan_registry(self) -> list[InstalledSoftware]:
        """扫描注册表 Uninstall 键。"""
        script = r"""
$paths = @(
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
$items = foreach ($p in $paths) {
    Get-ItemProperty $p -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -ne $null } |
    Select-Object DisplayName, DisplayVersion, InstallLocation, Publisher, UninstallString
}
$items | ConvertTo-Json -Depth 3 -Compress
"""
        try:
            raw: Any = run_powershell_json(script, timeout=60)
        except Exception as e:
            logger.warning("注册表扫描失败：{}", e)
            return []

        if raw is None:
            return []
        if isinstance(raw, dict):
            raw = [raw]

        result: list[InstalledSoftware] = []
        for item in raw:
            name = item.get("DisplayName")
            if not name:
                continue
            result.append(
                InstalledSoftware(
                    name=name.strip(),
                    version=(item.get("DisplayVersion") or "").strip() or None,
                    install_path=(item.get("InstallLocation") or "").strip() or None,
                    source=SoftwareSource.REGISTRY,
                    uninstall_string=(item.get("UninstallString") or "").strip() or None,
                    publisher=(item.get("Publisher") or "").strip() or None,
                )
            )
        return result

    def _scan_scoop(self) -> list[InstalledSoftware]:
        """扫描 Scoop 已装软件。"""
        script = r"""
if (Get-Command scoop -ErrorAction SilentlyContinue) {
    scoop export | ConvertFrom-Json | ForEach-Object { $_ } | ConvertTo-Json -Depth 5 -Compress
} else {
    ''
}
"""
        try:
            raw: Any = run_powershell_json(script, timeout=60)
        except Exception as e:
            logger.debug("Scoop 扫描失败（可能未安装）：{}", e)
            return []

        if not raw:
            return []

        apps = raw.get("apps", []) if isinstance(raw, dict) else []
        result: list[InstalledSoftware] = []
        for app in apps:
            name = app.get("Name")
            if not name:
                continue
            source = app.get("Source", "")
            bucket = app.get("Bucket", "")
            result.append(
                InstalledSoftware(
                    name=name,
                    version=app.get("Version"),
                    install_path=None,
                    source=SoftwareSource.SCOOP,
                    publisher=bucket or source or None,
                )
            )
        return result

    def _scan_winget(self) -> list[InstalledSoftware]:
        """扫描 winget 已装软件。"""
        script = r"""
if (Get-Command winget -ErrorAction SilentlyContinue) {
    winget list --accept-source-agreements --disable-interactivity |
    Select-Object -Skip 2 |
    ForEach-Object {
        $parts = $_ -split '\s{2,}'
        if ($parts.Count -ge 2) {
            [PSCustomObject]@{
                Name = $parts[0].Trim()
                Id = $parts[1].Trim()
                Version = if ($parts.Count -ge 3) { $parts[2].Trim() } else { $null }
            }
        }
    } | ConvertTo-Json -Depth 3 -Compress
} else {
    ''
}
"""
        try:
            raw: Any = run_powershell_json(script, timeout=90)
        except Exception as e:
            logger.debug("winget 扫描失败（可能未安装）：{}", e)
            return []

        if not raw:
            return []
        if isinstance(raw, dict):
            raw = [raw]

        result: list[InstalledSoftware] = []
        for item in raw:
            name = item.get("Name")
            if not name:
                continue
            result.append(
                InstalledSoftware(
                    name=name,
                    version=item.get("Version"),
                    install_path=None,
                    source=SoftwareSource.WINGET,
                    publisher=None,
                )
            )
        return result