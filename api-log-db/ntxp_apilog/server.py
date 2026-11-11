"""Local HTTP server for the NTXP API Log dashboard.

Serves the branded single-page dashboard and a small JSON API backed by the
shared SQLite DB. Stdlib only — no web framework.

Access control, in order of preference:
- **Google sign-in** (see `auth.py`): set `NTXP_APILOG_GOOGLE_CLIENT_ID` /
  `_SECRET` and an allowlist to require login. This is what makes it safe to
  share the dashboard on a network so "users can all share one database".
- **Loopback only** (default): with no OAuth configured, it binds to
  `127.0.0.1`; serving credentials on another interface prints a warning.

Either way, multiple people share the *data* by pointing `NTXP_APILOG_DB_PATH`
at the same synced file.
"""
from __future__ import annotations

import json
import os
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import auth as oauth
from .config import AUTH_TYPES, CATEGORIES, DEFAULT_HOST, DEFAULT_PORT, STATUSES
from .crypto import Cipher
from .db import connect, migrate
from .db.repository import Repository
from .model import ApiEntry, UsageEvent, parse_tags

DASHBOARD_HTML = Path(__file__).parent / "dashboard" / "index.html"


def _cookie_header(sid: str) -> str:
    secure = "; Secure" if os.environ.get("NTXP_APILOG_HTTPS") else ""
    return (f"{oauth.SESSION_COOKIE}={sid}; HttpOnly; SameSite=Lax; Path=/; "
            f"Max-Age={oauth.SESSION_TTL}{secure}")


def _clear_cookie_header() -> str:
    return f"{oauth.SESSION_COOKIE}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"


def _gate_page(title: str, message: str, show_login: bool) -> bytes:
    """A small NTXP-branded interstitial (sign-in / access-denied)."""
    button = ('<a class="btn" href="/auth/login">Sign in with Google</a>'
              if show_login else
              '<a class="btn" href="/auth/login">Try a different account</a>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>NTXP · {title}</title>
<style>body{{margin:0;height:100vh;display:grid;place-items:center;font-family:-apple-system,
BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#0b1f3a,#13294b);color:#fff}}
.card{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:16px;
padding:40px 44px;text-align:center;max-width:380px}}
.mark{{width:52px;height:52px;border-radius:11px;margin:0 auto 18px;display:grid;place-items:center;
font-weight:800;font-size:15px;color:#06243a;background:linear-gradient(135deg,#16b8a6,#3b82f6)}}
h1{{font-size:19px;margin:0 0 8px}}p{{color:#9fb3cc;font-size:14px;margin:0 0 24px}}
.btn{{display:inline-block;background:#16b8a6;color:#06243a;font-weight:700;text-decoration:none;
padding:11px 22px;border-radius:9px}}.btn:hover{{box-shadow:0 4px 14px rgba(22,184,166,.45)}}</style>
</head><body><div class="card"><div class="mark">NTXP</div><h1>{title}</h1>
<p>{message}</p>{button}</div></body></html>""".encode("utf-8")


def _make_handler(db_override: str | None, host: str, port: int):
    # One-time startup work (not per request): migrate the DB, build a single
    # Cipher (so the key file isn't re-read each request), cache the dashboard
    # HTML, and resolve the OAuth config + a session store.
    migrate(connect(db_override))
    shared_cipher = Cipher()
    dashboard_html = DASHBOARD_HTML.read_bytes() if DASHBOARD_HTML.exists() else None
    cfg = oauth.OAuthConfig.from_env(host, port)
    sessions = oauth.SessionStore()

    def repo() -> Repository:
        # A fresh connection per request keeps each worker thread isolated.
        return Repository(connect(db_override), cipher=shared_cipher)

    class Handler(BaseHTTPRequestHandler):
        server_version = "ntxp-apilog/0.1"

        # -- response helpers ------------------------------------------------
        def _send(self, code: int, body: bytes, ctype: str, headers: dict | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, obj, code: int = 200) -> None:
            self._send(code, json.dumps(obj, default=str).encode("utf-8"),
                       "application/json")

        def _redirect(self, location: str, headers: dict | None = None) -> None:
            self._send(302, b"", "text/plain", {**(headers or {}), "Location": location})

        def _read_body(self) -> dict:
            length = int(self.headers.get("Content-Length") or 0)
            if not length:
                return {}
            try:
                return json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return {}

        def log_message(self, *args):  # quiet by default
            pass

        # -- auth ------------------------------------------------------------
        def _session(self) -> dict | None:
            jar = SimpleCookie(self.headers.get("Cookie", ""))
            morsel = jar.get(oauth.SESSION_COOKIE)
            return sessions.get(morsel.value if morsel else None)

        def _guard(self, path: str) -> bool:
            """Return True if the request may proceed; otherwise respond and stop."""
            if not cfg.enabled or path.startswith("/auth/") or self._session():
                return True
            if path.startswith("/api/"):
                self._json({"error": "authentication required", "login": "/auth/login"}, 401)
            else:
                self._send(200, _gate_page("Sign in", "Sign in with your Google "
                           "account to access the NTXP API Log.", show_login=True),
                           "text/html; charset=utf-8")
            return False

        def _auth_route(self, path: str, qs: dict) -> bool:
            """Handle /auth/* GET routes. Returns True if it owned the path."""
            if path == "/auth/me":
                sess = self._session()
                self._json({"enabled": cfg.enabled, "authenticated": bool(sess),
                            "email": sess["email"] if sess else None,
                            "name": sess["name"] if sess else None})
            elif path == "/auth/login":
                self._redirect(oauth.authorize_url(cfg, sessions.new_state()))
            elif path == "/auth/logout":
                jar = SimpleCookie(self.headers.get("Cookie", ""))
                morsel = jar.get(oauth.SESSION_COOKIE)
                sessions.destroy(morsel.value if morsel else None)
                self._redirect("/", {"Set-Cookie": _clear_cookie_header()})
            elif path == "/auth/callback":
                self._auth_callback(qs)
            else:
                return False
            return True

        def _auth_callback(self, qs: dict) -> None:
            if not sessions.consume_state((qs.get("state") or [None])[0]):
                self._send(400, b"invalid or expired OAuth state", "text/plain")
                return
            code = (qs.get("code") or [None])[0]
            if not code:
                self._send(400, b"missing authorization code", "text/plain")
                return
            try:
                info = oauth.exchange_code(cfg, code)
            except Exception as exc:  # network/Google error
                self._send(502, f"OAuth exchange failed: {exc}".encode(), "text/plain")
                return
            email = info.get("email")
            if not info.get("email_verified") or not cfg.is_allowed(email):
                self._send(403, _gate_page("Access denied",
                           f"{email or 'That account'} is not authorized for this "
                           "API Log. Contact an admin to be added.", show_login=False),
                           "text/html; charset=utf-8")
                return
            sid = sessions.create(email, info.get("name") or email)
            self._redirect("/", {"Set-Cookie": _cookie_header(sid)})

        # -- routing ---------------------------------------------------------
        def do_GET(self):
            parsed = urlparse(self.path)
            path, qs = parsed.path, parse_qs(parsed.query)
            if path.startswith("/auth/") and self._auth_route(path, qs):
                return
            if not self._guard(path):
                return
            if path in ("/", "/index.html"):
                if dashboard_html is not None:
                    self._send(200, dashboard_html, "text/html; charset=utf-8")
                else:
                    self._send(500, b"dashboard html missing", "text/plain")
                return
            if path == "/api/meta":
                self._json({"categories": CATEGORIES, "auth_types": AUTH_TYPES,
                            "statuses": STATUSES})
                return
            if path == "/api/stats":
                self._json(repo().stats())
                return
            if path == "/api/apis":
                r = repo()
                q = (qs.get("q") or [""])[0]
                if q:
                    self._json(r.search(q, limit=int((qs.get("limit") or [100])[0])))
                else:
                    self._json(r.list_apis(
                        status=(qs.get("status") or [None])[0],
                        category=(qs.get("category") or [None])[0],
                    ))
                return
            if path.startswith("/api/apis/"):
                api_id = self._id_from(path, suffix="")
                if api_id is not None:
                    api = repo().get_api(api_id, reveal=False)
                    self._json(api or {"error": "not found"}, 200 if api else 404)
                    return
            self._json({"error": "not found"}, 404)

        def do_POST(self):
            path = urlparse(self.path).path
            if not self._guard(path):
                return
            body = self._read_body()

            if path == "/api/apis":
                self._upsert(body)
                return
            if path.startswith("/api/apis/") and path.endswith("/reveal"):
                api_id = self._id_from(path, suffix="/reveal")
                if api_id is not None:
                    r = repo()
                    api = r.get_api(api_id, reveal=True)
                    if not api:
                        self._json({"error": "not found"}, 404)
                        return
                    r.log_access(api_id, action="reveal",
                                 accessor=body.get("accessor") or self._accessor(),
                                 purpose=body.get("purpose"), origin="dashboard")
                    self._json(api)
                    return
            if path.startswith("/api/apis/") and path.endswith("/usage"):
                api_id = self._id_from(path, suffix="/usage")
                if api_id is not None:
                    r = repo()
                    log_id = r.log_usage(UsageEvent(
                        api_id=api_id, cost=float(body.get("cost") or 0),
                        units=body.get("units"), unit_kind=body.get("unit_kind"),
                        description=body.get("description"),
                        requested_by=body.get("requested_by"), origin="dashboard",
                    ))
                    self._json({"log_id": log_id})
                    return
            self._json({"error": "not found"}, 404)

        def do_DELETE(self):
            path = urlparse(self.path).path
            if not self._guard(path):
                return
            if path.startswith("/api/apis/"):
                api_id = self._id_from(path, suffix="")
                if api_id is not None:
                    repo().delete_api(api_id)
                    self._json({"ok": True})
                    return
            self._json({"error": "not found"}, 404)

        # -- shared ----------------------------------------------------------
        def _accessor(self) -> str | None:
            """Attribute audited reveals to the signed-in user when available."""
            sess = self._session()
            return f"user:{sess['email']}" if sess else None

        def _id_from(self, path: str, suffix: str) -> int | None:
            tail = path.removeprefix("/api/apis/").removesuffix(suffix).strip("/")
            return int(tail) if tail.isdigit() else None

        def _upsert(self, body: dict) -> None:
            if not body.get("name"):
                self._json({"error": "name is required"}, 400)
                return
            entry = ApiEntry(
                name=body["name"], provider=body.get("provider"),
                category=body.get("category"), base_url=body.get("base_url"),
                docs_url=body.get("docs_url"), login_url=body.get("login_url"),
                purpose=body.get("purpose"), auth_type=body.get("auth_type") or "api_key",
                api_key=body.get("api_key") or None,
                key_number=body.get("key_number") or None,
                login_user=body.get("login_user") or None,
                login_secret=body.get("login_secret") or None,
                cost_model=body.get("cost_model"), currency=body.get("currency") or "USD",
                monthly_budget=body.get("monthly_budget"),
                owner=body.get("owner") or (self._session() or {}).get("email"),
                tags=parse_tags(body.get("tags")), notes=body.get("notes"),
            )
            api_id, is_new = repo().upsert_api(entry, origin="dashboard")
            self._json({"api_id": api_id, "is_new": is_new})

    return Handler


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
          db_override: str | None = None) -> None:
    handler = _make_handler(db_override, host, port)
    httpd = ThreadingHTTPServer((host, port), handler)
    cfg = oauth.OAuthConfig.from_env(host, port)
    if cfg.enabled:
        print(f"Google sign-in required. Authorized redirect URI: {cfg.redirect_uri}")
        if not cfg.allowed_emails and not cfg.allowed_domain:
            print("WARNING: no allowlist set — ANY Google account can sign in. "
                  "Set NTXP_APILOG_ALLOWED_EMAILS or NTXP_APILOG_ALLOWED_DOMAIN.")
    elif host not in ("127.0.0.1", "localhost", "::1"):
        print(f"WARNING: serving live credentials on {host} with no Google sign-in. "
              "Set NTXP_APILOG_GOOGLE_CLIENT_ID/_SECRET, or bind to loopback.")
    print(f"NTXP API Log dashboard → http://{host}:{port}  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
