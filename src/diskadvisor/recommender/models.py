"""推荐结果模型。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Risk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecCategory(str, Enum):
    INSTALL = "install"
    MIGRATE = "migrate"
    ENV = "env"
    CONFIG = "config"


class Step(BaseModel):
    """执行步骤。"""

    order: int
    description: str
    command: str | None = None
    manual: bool = False
    warning: str | None = None


class Recommendation(BaseModel):
    """单条推荐。"""

    id: str
    priority: Priority = Priority.MEDIUM
    category: RecCategory
    title: str
    reason: str = ""
    impact_gb: float = 0.0
    difficulty: Difficulty = Difficulty.EASY
    risk: Risk = Risk.LOW
    steps: list[Step] = Field(default_factory=list)
    auto_executable: bool = False
    estimated_minutes: int = 5
    rollback: str | None = None
    kb_ref: str | None = None
    score: float = 0.0
    conflict: str | None = None


class InstallationAdvice(BaseModel):
    """单个软件的安装建议。"""

    software_id: str
    software_name: str
    recommended_install_path: str
    recommended_data_path: str | None = None
    install_method: str | None = None
    install_command: str | None = None
    env_vars: list[dict[str, str]] = Field(default_factory=list)
    version_management: dict | None = None
    migration_steps: list[str] = Field(default_factory=list)
    notes: str = ""
    already_installed: bool = False
    current_path: str | None = None
    is_misplaced: bool = False