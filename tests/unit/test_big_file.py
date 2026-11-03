"""大文件扫描器测试。"""

from pathlib import Path

from diskadvisor.scanner.big_file import BigFileScanner


def test_big_file_scanner(tmp_path: Path) -> None:
    (tmp_path / "huge.bin").write_bytes(b"0" * (2 * 1024 * 1024))  # 2MB
    (tmp_path / "tiny.txt").write_text("hi")

    scanner = BigFileScanner(
        roots=[str(tmp_path)],
        threshold_gb=0.001,
        max_results=10,
    )
    result = scanner.scan()

    assert len(result) == 1
    assert result[0].path.endswith("huge.bin")