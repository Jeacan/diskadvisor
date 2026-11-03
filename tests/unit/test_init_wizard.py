"""初始化向导测试。"""

from diskadvisor.cli.init_wizard import InitWizard
from diskadvisor.core.config.settings import Settings


def test_generate_script() -> None:
    settings = Settings(
        developer_root="D:\\Developer",
        scoop_root="D:\\Developer\\Scoop",
        scoop_global_root="D:\\Developer\\ScoopGlobal",
    )
    wizard = InitWizard(settings)
    script = wizard.generate_setup_script()

    assert "DiskAdvisor 新机初始化脚本" in script
    assert "D:\\Developer\\Scoop" in script
    assert "SetEnvironmentVariable" in script
    assert "irm get.scoop.sh" in script


def test_get_directories() -> None:
    wizard = InitWizard()
    dirs = wizard.get_directories()
    assert len(dirs) >= 5
    assert all(d.startswith("D:") for d in dirs)