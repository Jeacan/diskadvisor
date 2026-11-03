"""规划方案导出/导入测试。"""

from pathlib import Path

from diskadvisor.core.config.plan import PlanManager
from diskadvisor.core.config.settings import Settings


def test_export_and_import(tmp_path: Path) -> None:
    settings = Settings(developer_root="E:\\Dev", scoop_root="E:\\Dev\\Scoop")
    manager = PlanManager()

    output = tmp_path / "plan.json"
    manager.export(settings, output)
    assert output.exists()

    loaded = manager.import_plan(output)
    assert loaded.developer_root == "E:\\Dev"
    assert loaded.scoop_root == "E:\\Dev\\Scoop"


def test_import_nonexistent(tmp_path: Path) -> None:
    manager = PlanManager()
    try:
        manager.import_plan(tmp_path / "nope.json")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("应该抛 FileNotFoundError")