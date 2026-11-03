"""目录扫描器测试。"""

from pathlib import Path

from diskadvisor.scanner.dir_size import DirSizeScanner


def test_dir_size_scanner(tmp_path: Path) -> None:
    # 创建测试目录结构
    (tmp_path / "big").mkdir()
    (tmp_path / "big" / "file.bin").write_bytes(b"0" * (2 * 1024 * 1024))  # 2MB

    (tmp_path / "small").mkdir()
    (tmp_path / "small" / "file.txt").write_text("hello")

    scanner = DirSizeScanner(roots=[str(tmp_path)], top_n=5, min_size_gb=0)
    result = scanner.scan()

    assert len(result) >= 2
    assert result[0].size_gb >= result[1].size_gb
    assert result[0].path.endswith("big")