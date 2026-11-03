"""知识库测试。"""

from diskadvisor.kb import KnowledgeBase, SoftwareCategory


def test_kb_load() -> None:
    kb = KnowledgeBase()
    kb.load()
    entries = kb.all()
    assert len(entries) >= 20


def test_kb_get_wechat() -> None:
    kb = KnowledgeBase()
    entry = kb.get("wechat")
    assert entry is not None
    assert entry.name == "微信"
    assert entry.category == SoftwareCategory.SOCIAL


def test_kb_search() -> None:
    kb = KnowledgeBase()
    results = kb.search("node")
    assert len(results) >= 1
    assert any(e.id == "nodejs" for e in results)


def test_kb_match_by_name() -> None:
    kb = KnowledgeBase()
    entry = kb.match_by_name("微信")
    assert entry is not None
    assert entry.id == "wechat"


def test_kb_match_by_alias() -> None:
    kb = KnowledgeBase()
    entry = kb.match_by_name("VSCode")
    assert entry is not None
    assert entry.id == "vscode"