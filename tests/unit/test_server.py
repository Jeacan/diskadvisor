"""Web API 测试。"""

from fastapi.testclient import TestClient

from diskadvisor.server import create_app


def test_version() -> None:
    client = TestClient(create_app())
    res = client.get("/api/version")
    assert res.status_code == 200
    assert "version" in res.json()


def test_kb_list() -> None:
    client = TestClient(create_app())
    res = client.get("/api/kb/list")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 20
    assert any(e["id"] == "wechat" for e in data)


def test_kb_search() -> None:
    client = TestClient(create_app())
    res = client.get("/api/kb/search?q=node")
    assert res.status_code == 200
    assert any(e["id"] == "nodejs" for e in res.json())


def test_advise_wechat() -> None:
    client = TestClient(create_app())
    res = client.get("/api/advise/wechat")
    assert res.status_code == 200
    data = res.json()
    assert data["software_id"] == "wechat"


def test_advise_not_found() -> None:
    client = TestClient(create_app())
    res = client.get("/api/advise/nonexistent-xyz")
    assert res.status_code == 404


def test_index() -> None:
    client = TestClient(create_app())
    res = client.get("/")
    assert res.status_code == 200
    assert "DiskAdvisor" in res.text