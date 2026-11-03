"""规划方案导出/导入。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from diskadvisor.core.config.settings import Settings


class PlanExport(BaseModel):
    """导出的规划方案。"""

    version: str = "1"
    exported_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    settings: dict = Field(default_factory=dict)


class PlanManager:
    """规划方案管理。"""

    def export(self, settings: Settings, output: Path) -> None:
        """导出配置。"""
        plan = PlanExport(settings=settings.model_dump(mode="json"))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    def import_plan(self, input_path: Path) -> Settings:
        """导入配置。"""
        if not input_path.exists():
            raise FileNotFoundError(f"文件不存在：{input_path}")

        data = json.loads(input_path.read_text(encoding="utf-8"))
        plan = PlanExport(**data)
        return Settings(**plan.settings)