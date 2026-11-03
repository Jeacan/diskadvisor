"""知识库数据模型。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SoftwareCategory(str, Enum):
    SOCIAL = "social"
    GAME = "game"
    DEV = "dev"
    OFFICE = "office"
    ENTERTAINMENT = "entertainment"
    SYSTEM = "system"
    GREEN = "green"
    OTHER = "other"


class InstallMethodType(str, Enum):
    SCOOP = "scoop"
    WINGET = "winget"
    CHOCO = "choco"
    MANUAL = "manual"


class MigrationRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InstallMethod(BaseModel):
    method: InstallMethodType
    command: str | None = None
    priority: int = 1


class Migration(BaseModel):
    install: str = "none"
    data: str = "none"
    steps: list[str] = Field(default_factory=list)
    risk: MigrationRisk = MigrationRisk.LOW
    auto_migratable: bool = False


class EnvVarSpec(BaseModel):
    name: str
    value: str
    scope: str = "user"


class VersionManagement(BaseModel):
    tool: str = ""
    method: str = ""
    commands: list[str] = Field(default_factory=list)


class SoftwareEntry(BaseModel):
    """单个软件的知识库条目。"""

    id: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    category: SoftwareCategory
    defaultInstallPaths: list[str] = Field(default_factory=list)
    defaultDataPaths: list[str] = Field(default_factory=list)
    recommendedInstallPath: str
    recommendedDataPath: str | None = None
    installMethods: list[InstallMethod] = Field(default_factory=list)
    migration: Migration = Field(default_factory=Migration)
    envVars: list[EnvVarSpec] = Field(default_factory=list)
    versionManagement: VersionManagement | None = None
    notes: str = ""
    verifiedVersion: str = ""
    verifiedDate: str = ""