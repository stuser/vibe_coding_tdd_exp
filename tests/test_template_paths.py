import importlib
import sys

from fastapi.testclient import TestClient


def test_should_render_template_when_cwd_diff(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sys.modules.pop("app.main", None)
    main = importlib.import_module("app.main")
    client = TestClient(main.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Trip Splitter" in resp.content
