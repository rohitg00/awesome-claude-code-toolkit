"""/assets route (the engine's logo, mounted at deploy time) and the dark-by-default page shells."""
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from ntxp_contracts.web.server import make_handler


@pytest.fixture()
def base(tmp_path, monkeypatch):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "ntxp_logo_reversed.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (assets / "notes.txt").write_text("nope")
    (tmp_path / "secret.png").write_bytes(b"secret")
    monkeypatch.setenv("NTXP_ASSETS_DIR", str(assets))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(str(tmp_path / "c.db")))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def test_logo_served_with_type_and_nosniff(base):
    code, h, body = get(base + "/assets/ntxp_logo_reversed.png")
    assert code == 200 and h["Content-Type"] == "image/png" and body.startswith(b"\x89PNG")
    assert h["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize("p", ["/assets/notes.txt", "/assets/..%2Fsecret.png", "/assets/../secret.png",
                               "/assets/missing.png", "/assets/%2e%2e/secret.png", "/assets/"])
def test_assets_reject_traversal_unknown_types_and_missing(base, p):
    assert get(base + p)[0] == 404


def test_assets_404_when_not_configured(base, monkeypatch):
    monkeypatch.delenv("NTXP_ASSETS_DIR")
    assert get(base + "/assets/ntxp_logo_reversed.png")[0] == 404


def test_pages_are_dark_by_default_and_link_the_engine_logo_zone(base):
    for path in ("/", "/contract?id=1"):
        code, _, body = get(base + path)
        html = body.decode()
        assert code == 200 and 'data-theme="dark"' in html and 'id="logo"' in html
        assert "Open+Sans" in html and 'class="accent"' in html


def test_brand_js_no_longer_repaints_the_engine_tokens(base):
    js = get(base + "/static/brand.js")[2].decode()
    assert "/api/branding" not in js and "setProperty" not in js
    assert "/assets/ntxp_logo_reversed.png" in js
