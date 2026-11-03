"""路径工具测试。"""

from diskadvisor.core.utils.paths import is_subpath, normalize_path


def test_is_subpath_true() -> None:
    assert is_subpath("D:\\Developer\\Scoop\\apps", "D:\\Developer") is True


def test_is_subpath_false() -> None:
    assert is_subpath("C:\\Windows", "D:\\Developer") is False


def test_normalize_path() -> None:
    assert normalize_path("D:/Developer/Scoop/") == "D:\\Developer\\Scoop"