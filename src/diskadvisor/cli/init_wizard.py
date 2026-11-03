"""新机初始化向导。"""

from __future__ import annotations

from pathlib import Path

from diskadvisor.core.config.settings import Settings


class InitWizard:
    """交互式初始化向导。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def get_directories(self) -> list[str]:
        """获取要创建的目录列表。"""
        s = self.settings
        return [
            s.developer_root,
            s.scoop_root,
            s.scoop_global_root,
            s.social_root,
            s.games_root,
            s.entertainment_root,
            s.office_root,
            s.green_root,
            s.system_tools_root,
        ]

    def generate_setup_script(self) -> str:
        """生成初始化脚本。"""
        lines: list[str] = []
        lines.append("# DiskAdvisor 新机初始化脚本")
        lines.append("# 请审阅后执行")
        lines.append("")
        lines.append('$ErrorActionPreference = "Stop"')
        lines.append("")

        lines.append("# 1. 创建目录结构")
        for d in self.get_directories():
            lines.append(f'New-Item -ItemType Directory -Path "{d}" -Force | Out-Null')
            lines.append(f'Write-Host "已创建：{d}"')
        lines.append("")

        lines.append("# 2. 配置 Scoop 环境变量")
        lines.append(
            f'[Environment]::SetEnvironmentVariable("SCOOP", "{self.settings.scoop_root}", "User")'
        )
        lines.append(
            f'[Environment]::SetEnvironmentVariable("SCOOP_GLOBAL", "{self.settings.scoop_global_root}", "Machine")'
        )
        lines.append('Write-Host "已配置 SCOOP 环境变量"')
        lines.append("")

        lines.append("# 3. 安装 Scoop")
        lines.append('Write-Host "即将安装 Scoop..."')
        lines.append("irm get.scoop.sh | iex")
        lines.append("")

        lines.append("# 4. 设置缓存目录")
        lines.append(f'scoop config cache_path "{self.settings.scoop_root}\\cache"')
        lines.append('Write-Host "Scoop 配置完成"')
        lines.append("")

        lines.append('Write-Host "初始化完成！请重启 PowerShell 使环境变量生效。"')

        return "\n".join(lines)

    def save_script(self, output: Path) -> None:
        """保存脚本。"""
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.generate_setup_script(), encoding="utf-8-sig")