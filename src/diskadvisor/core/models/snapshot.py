"""系统快照数据模型。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DiskType(str, Enum):
    """磁盘类型。"""

    SSD = "SSD"
    HDD = "HDD"
    UNKNOWN = "Unknown"


class SoftwareSource(str, Enum):
    """软件来源。"""

    REGISTRY = "registry"
    SCOOP = "scoop"
    WINGET = "winget"
    STORE = "store"
    UNKNOWN = "unknown"


class EnvScope(str, Enum):
    """环境变量作用域。"""

    PROCESS = "process"
    USER = "user"
    MACHINE = "machine"


class DiskInfo(BaseModel):
    """单个磁盘信息。"""

    letter: str = Field(description="盘符，如 C、D")
    total_gb: float = Field(description="总容量 GB")
    free_gb: float = Field(description="可用容量 GB")
    used_percent: float = Field(description="使用率 0-100")
    disk_type: DiskType = Field(default=DiskType.UNKNOWN, description="磁盘类型")
    is_system: bool = Field(default=False, description="是否为系统盘")
    label: str | None = Field(default=None, description="卷标")


class InstalledSoftware(BaseModel):
    """已安装软件。"""

    name: str
    version: str | None = None
    install_path: str | None = None
    source: SoftwareSource = SoftwareSource.UNKNOWN
    uninstall_string: str | None = None
    publisher: str | None = None


class EnvVar(BaseModel):
    """环境变量。"""

    name: str
    value: str
    scope: EnvScope


class DirSize(BaseModel):
    """目录占用。"""

    path: str
    size_gb: float
    file_count: int = 0


class BigFile(BaseModel):
    """大文件。"""

    path: str
    size_gb: float


class SystemSnapshot(BaseModel):
    """系统现状快照。"""

    timestamp: datetime = Field(default_factory=datetime.now)
    os_version: str = ""
    os_build: str = ""
    user_profile: str = ""
    computer_name: str = ""
    is_admin: bool = False

    disks: list[DiskInfo] = Field(default_factory=list)
    installed: list[InstalledSoftware] = Field(default_factory=list)
    env_vars: list[EnvVar] = Field(default_factory=list)
    top_dirs: list[DirSize] = Field(default_factory=list)
    big_files: list[BigFile] = Field(default_factory=list)