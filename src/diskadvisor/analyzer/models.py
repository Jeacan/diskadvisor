"""分析结果模型。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PressureLevel(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    OK = "ok"


class DiskPressure(BaseModel):
    letter: str
    level: PressureLevel
    free_gb: float
    used_percent: float
    message: str


class SpaceAttribution(BaseModel):
    """空间归因：某目录属于哪个软件。"""

    path: str
    size_gb: float
    software_id: str | None = None
    software_name: str | None = None
    category: str = "unknown"


class MisplacedSoftware(BaseModel):
    """位置不正确的软件。"""

    software_id: str
    software_name: str
    current_path: str
    recommended_path: str
    reason: str


class AnalysisResult(BaseModel):
    """分析结果。"""

    disk_pressures: list[DiskPressure] = Field(default_factory=list)
    attributions: list[SpaceAttribution] = Field(default_factory=list)
    misplaced: list[MisplacedSoftware] = Field(default_factory=list)
    env_issues: list[str] = Field(default_factory=list)