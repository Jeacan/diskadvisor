"""知识库校验器测试。"""

from pathlib import Path

from diskadvisor.kb.validator import KBValidator


def test_validate_builtin_kb() -> None:
    """内置知识库应该无错误。"""
    validator = KBValidator()
    issues = validator.validate()
    errors = [i for i in issues if i.level == "error"]
    assert len(errors) == 0


def test_validate_bad_json(tmp_path: Path) -> None:
    """非法 JSON 应该被捕获。"""
    (tmp_path / "bad.json").write_text("{invalid", encoding="utf-8")
    validator = KBValidator(entries_dir=tmp_path)
    issues = validator.validate()
    assert any(i.level == "error" for i in issues)


def test_validate_duplicate_id(tmp_path: Path) -> None:
    """重复 ID 应该被捕获。"""
    import json

    entry = {
        "id": "test",
        "name": "Test",
        "category": "dev",
        "recommendedInstallPath": "D:\\Test",
    }
    (tmp_path / "a.json").write_text(json.dumps(entry), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps(entry), encoding="utf-8")

    validator = KBValidator(entries_dir=tmp_path)
    issues = validator.validate()
    assert any("ID 重复" in i.message for i in issues)