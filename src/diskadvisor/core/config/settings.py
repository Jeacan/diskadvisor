"""用户配置。"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """DiskAdvisor 配置。"""

    model_config = SettingsConfigDict(
        env_prefix="DISKADVISOR_",
        env_file=".env",
        extra="ignore",
    )

    # 目标目录规划
    d_drive_root: str = Field(default="D:\\")
    developer_root: str = Field(default="D:\\Developer")
    social_root: str = Field(default="D:\\SocialApps")
    games_root: str = Field(default="D:\\Games")
    entertainment_root: str = Field(default="D:\\Entertainment")
    office_root: str = Field(default="D:\\Office")
    green_root: str = Field(default="D:\\GreenSoft")
    system_tools_root: str = Field(default="D:\\SystemTools")

    # Scoop
    scoop_root: str = Field(default="D:\\Developer\\Scoop")
    scoop_global_root: str = Field(default="D:\\Developer\\ScoopGlobal")

    # 扫描选项
    top_dir_count: int = Field(default=10, description="目录占用 Top N")
    big_file_threshold_gb: float = Field(default=0.5, description="大文件阈值 GB")
    scan_timeout_seconds: int = Field(default=300, description="扫描超时")

    # 输出
    output_dir: Path = Field(default=Path("report"))