"""Stateless streamable-HTTP MCP app, gated by a Bearer OAuth token.

The MCP tools are the same ones the stdio server exposes (search/get/upsert/
reconcile/qualify/enrich/context/locate …). Statelessness means every request
stands alone — all state lives in the canonical DB — so this scales horizontally
on the VPS with no server-side session store.
"""
from __future__ import annotations

import json

from .auth import verify_token, verify_token_async

_OPEN_PATHS = ("/health", "/healthz", "/.well-known/")


async def _send_json(send, status: int, body: dict) -> None:
    payload = json.dumps(body).encode()
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json"),
                            (b"content-length", str(len(payload)).encode())]})
    await send({"type": "http.response.body", "body": payload})


class AuthMiddleware:
    """Pure-ASGI Bearer-token gate. Imports no server deps, so it is unit-testable
    on its own with a stub inner app."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        if any(path.startswith(p) or path.rstrip("/").endswith("/health") for p in _OPEN_PATHS):
            return await _send_json(send, 200, {"ok": True, "service": "ntxp-contacts-mcp"})
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers") or []}
        auth = headers.get("authorization", "")
        token = auth[7:].strip() if auth[:7].lower() == "bearer " else ""
        if await verify_token_async(token) is None:
            return await _send_json(send, 401, {
                "error": "unauthorized",
                "detail": "Bearer Google Workspace (ntxpllc.com) OAuth token required.",
            })
        return await self.app(scope, receive, send)


SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"x-frame-options", b"DENY"),
    (b"content-security-policy", (
        b"default-src 'self'; script-src 'self' 'unsafe-inline' https://accounts.google.com; "
        b"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        b"font-src https://fonts.gstatic.com; img-src 'self' data: https:; "
        b"connect-src 'self' https://accounts.google.com https://www.googleapis.com; "
        b"frame-src https://accounts.google.com; frame-ancestors 'none'; base-uri 'none'")),
]


def _page_path():
    """The React build (web/dist/index.html, made by `npm run build` in web-app/) when present,
    else the dependency-free legacy page so a source checkout still works."""
    from importlib import resources
    web = resources.files("ntxp_contacts").joinpath("web")
    built = web.joinpath("dist/index.html")
    return built if built.is_file() else web.joinpath("index.html")


_APP_TYPES = {".js": "application/javascript", ".css": "text/css", ".map": "application/json",
              ".woff2": "font/woff2", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon"}


async def _app_file(send, rel: str):
    """Serve a built front-end file from web/dist (hashed names → immutable cache). Whitelisted
    filenames only; no traversal. Brand assets are NOT here — they come from /assets (mounted)."""
    import re
    from importlib import resources
    parts = [p for p in rel.split("/") if p]
    ext = "." + parts[-1].rsplit(".", 1)[-1].lower() if parts and "." in parts[-1] else ""
    if (not parts or len(parts) > 3 or ext not in _APP_TYPES
            or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in (".", "..") for p in parts)):
        return await _send_bytes(send, 404, "text/plain", b"not found")
    f = resources.files("ntxp_contacts").joinpath("web/dist", *parts)
    if not f.is_file():
        return await _send_bytes(send, 404, "text/plain", b"not found")
    data = f.read_bytes()
    await send({"type": "http.response.start", "status": 200,
                "headers": [(b"content-type", _APP_TYPES[ext].encode()), (b"content-length", str(len(data)).encode()),
                            (b"cache-control", b"public, max-age=31536000, immutable")] + list(SECURITY_HEADERS)})
    await send({"type": "http.response.body", "body": data})


_ASSET_TYPES = {".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon",
                ".woff2": "font/woff2"}


async def _asset(send, name: str):
    """Serve a brand asset (logo) from NTXP_ASSETS_DIR. The NTXP logo/fonts are
    proprietary and are NOT committed to this repo — the deploy script copies them
    from the installed NTXP Branded Document skill. Filename-whitelisted."""
    import os
    import re
    base = os.environ.get("NTXP_ASSETS_DIR")
    ext = os.path.splitext(name)[1].lower()
    if not base or not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or ext not in _ASSET_TYPES:
        return await _send_bytes(send, 404, "text/plain", b"not found")
    path = os.path.join(base, name)
    if not os.path.isfile(path):
        return await _send_bytes(send, 404, "text/plain", b"not found")
    with open(path, "rb") as fh:
        data = fh.read()
    await send({"type": "http.response.start", "status": 200,
                "headers": [(b"content-type", _ASSET_TYPES[ext].encode()),
                            (b"content-length", str(len(data)).encode()),
                            (b"cache-control", b"public, max-age=86400")] + list(SECURITY_HEADERS)})
    await send({"type": "http.response.body", "body": data})


def _config_js() -> bytes:
    import os
    cfg = {"clientId": os.environ.get("NTXP_GOOGLE_CLIENT_ID", ""),
           "domain": os.environ.get("NTXP_MCP_ALLOWED_DOMAIN", "ntxpllc.com"),
           # dev = server runs with NTXP_MCP_AUTH=none: skip Google sign-in (local preview only)
           "dev": os.environ.get("NTXP_MCP_AUTH", "google").lower() == "none"}
    return ("window.NTXP_CONFIG=" + json.dumps(cfg) + ";").encode()


async def _send_bytes(send, status: int, ctype: str, body: bytes, extra=()):
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", ctype.encode()),
                            (b"content-length", str(len(body)).encode()),
                            (b"cache-control", b"no-store")] + list(SECURITY_HEADERS) + list(extra)})
    await send({"type": "http.response.body", "body": body})


class ApiApp:
    """Auth-gated JSON API (see remote/api.py). One DB connection per request;
    migrations run once per process."""

    def __init__(self, db_override=None):
        self.db_override = db_override
        self._ready = False
        self._lock = __import__("threading").Lock()

    def _conn(self):
        from ..db import connect, migrate
        c = connect(self.db_override)
        if not self._ready:
            with self._lock:                      # concurrent first requests must not both run the migrations
                if not self._ready:
                    migrate(c)
                    self._ready = True
        return c

    async def __call__(self, scope, receive, send):
        import asyncio
        from .api import handle, parse_query
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers") or []}
        auth = headers.get("authorization", "")
        token = auth[7:].strip() if auth[:7].lower() == "bearer " else ""
        path = scope["path"]
        inbound = path.startswith("/api/v1/hooks/in/")          # peers authenticate by HMAC signature
        is_v1 = path.startswith("/api/v1/")
        # A peer service token is honoured on /api/v1 only; the human /api never accepts it.
        user = None if inbound else await verify_token_async(token, allow_service=is_v1)
        if user is None and not inbound:
            return await _send_bytes(send, 401, "application/json",
                                     b'{"error":"unauthorized","detail":"Sign in with your ntxpllc.com Google account."}')
        body = b""
        more = True
        while more:
            msg = await receive()
            body += msg.get("body", b"")
            more = msg.get("more_body", False)
            if len(body) > 1_000_000:
                return await _send_bytes(send, 413, "application/json", b'{"error":"too large"}')
        query = parse_query((scope.get("query_string") or b"").decode())

        if inbound:
            if scope["method"] != "POST":
                return await _send_bytes(send, 405, "application/json", b'{"error":"POST only"}')

            def run_in():
                from ..peers import inbound as _in, load_peers
                conn = self._conn()
                try:
                    st, obj = _in.handle(conn, load_peers()[0], path.rsplit("/", 1)[1], body, headers)
                    return st, "application/json", json.dumps(obj).encode()
                finally:
                    conn.close()
            status, ctype, data = await asyncio.to_thread(run_in)
            return await _send_bytes(send, status, ctype, data)

        try:
            payload = json.loads(body) if body else {}
        except ValueError:
            return await _send_bytes(send, 400, "application/json", b'{"error":"bad json"}')

        def run():
            conn = self._conn()
            try:
                if is_v1:
                    from .api import ApiError, _json
                    from .peer_api import handle_v1
                    try:
                        return handle_v1(conn, user, scope["method"], path, query)
                    except ApiError as e:
                        return _json(e.status, {"error": e.msg})
                return handle(conn, user["email"], scope["method"], path, query, payload)
            finally:
                conn.close()

        status, ctype, data = await asyncio.to_thread(run)
        await _send_bytes(send, status, ctype, data)


def build_http_app(db_override=None):
    """Return the ASGI app (requires the `mcp` extra):
      /            the live contacts page (static) + /config.js   (open; sign-in is client-side)
      /api/*       JSON API behind the Google Workspace token gate
      /mcp         stateless MCP (token-gated)
      /carddav     read-only CardDAV for one-way iOS sync (token-gated)
      /health      open
    """
    from ..mcp_server import build_server
    from .carddav import CardDAVApp
    mcp_app = AuthMiddleware(build_server(db_override, stateless_http=True).streamable_http_app())
    carddav = CardDAVApp(db_override)
    api = ApiApp(db_override)
    from ..peers.runner import start_background
    start_background(db_override)      # contracts watch + outbound webhook delivery, when peers are configured

    async def dispatch(scope, receive, send):
        if scope.get("type") != "http":
            return await mcp_app(scope, receive, send)
        path = scope.get("path", "")
        if path in ("/", "/index.html"):
            return await _send_bytes(send, 200, "text/html; charset=utf-8",
                                     _page_path().read_bytes())
        if path.startswith("/app/"):
            return await _app_file(send, path[len("/app/"):])
        if path.startswith("/assets/"):
            return await _asset(send, path[len("/assets/"):])
        if path == "/config.js":
            return await _send_bytes(send, 200, "application/javascript", _config_js())
        if path.startswith("/api/"):
            return await api(scope, receive, send)
        if path.startswith("/carddav") or path == "/.well-known/carddav":
            return await carddav(scope, receive, send)
        return await mcp_app(scope, receive, send)

    return dispatch


def serve(db_override=None, host: str = "0.0.0.0", port: int = 8080) -> None:
    try:
        import uvicorn
    except Exception as exc:  # pragma: no cover
        raise SystemExit("uvicorn is required: pip install 'ntxp-contacts[remote]'") from exc
    uvicorn.run(build_http_app(db_override), host=host, port=port)
