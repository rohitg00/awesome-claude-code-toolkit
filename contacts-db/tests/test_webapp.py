"""Static serving of the React build (/app/*) and the page fallback."""
import asyncio

import pytest

from ntxp_contacts.remote import http_server as hs


def _get(path):
    """Call the /app/ static handler directly and collect status, headers and body."""
    out = {"body": b""}

    async def send(m):
        if m["type"] == "http.response.start":
            out["status"], out["headers"] = m["status"], dict(m["headers"])
        else:
            out["body"] += m.get("body", b"")

    assert path.startswith("/app/")
    asyncio.run(hs._app_file(send, path[len("/app/"):]))
    return out


@pytest.fixture()
def fake_dist(tmp_path, monkeypatch):
    web = tmp_path / "ntxp_contacts" / "web"
    (web / "dist" / "assets").mkdir(parents=True)
    (web / "dist" / "index.html").write_text("<!doctype html><title>react</title>")
    (web / "dist" / "assets" / "index-abc.js").write_text("console.log(1)")
    (web / "index.html").write_text("<!doctype html><title>legacy</title>")
    (tmp_path / "secret.txt").write_text("nope")

    import importlib.resources as r
    monkeypatch.setattr(r, "files", lambda pkg: tmp_path / "ntxp_contacts")
    return tmp_path


def test_app_serves_built_assets_with_types_and_immutable_cache(fake_dist):
    o = _get("/app/assets/index-abc.js")
    assert o["status"] == 200 and o["body"] == b"console.log(1)"
    assert o["headers"][b"content-type"] == b"application/javascript"
    assert b"immutable" in o["headers"][b"cache-control"]


@pytest.mark.parametrize("p", ["/app/../secret.txt", "/app/assets/../../secret.txt", "/app/%2e%2e/secret.txt",
                               "/app/assets/index-abc.exe", "/app/", "/app/assets/missing.js", "/app/a/b/c/d.js"])
def test_app_rejects_traversal_unknown_types_and_missing(fake_dist, p):
    assert _get(p)["status"] == 404


def test_page_prefers_the_react_build_and_falls_back_to_legacy(fake_dist):
    assert "react" in hs._page_path().read_text()
    (fake_dist / "ntxp_contacts" / "web" / "dist" / "index.html").unlink()
    assert "legacy" in hs._page_path().read_text()
