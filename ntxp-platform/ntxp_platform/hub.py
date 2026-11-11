"""Hub: one codebase, many subdomains.

* ``dispatch(registry, qualified, args, view)`` — the single in-process tool-call path used by
  the MCP server, the CLI and the HTTP hub. It enforces view scoping and the secret/sensitive
  rules, so no entry point can bypass them.
* ``HubHandler`` — stdlib HTTP server: ``/_ntxp/profile``, ``/_ntxp/call`` (bearer-gated) and
  Host-header routing of everything else to per-app upstreams (the apps' own servers), so the
  same container image can serve every subdomain as a different view.
"""
from __future__ import annotations

import hmac
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .registry import Registry, load_registry
from .views import VIEWS, allowed


class Denied(Exception):
    pass


def dispatch(reg: Registry, qualified: str, args: dict | None = None, view: str = "all",
             allow_write: bool = False):
    fn = reg.function(qualified)
    if fn.sensitive:
        raise Denied(f"{qualified} reveals secrets and is only available inside its own app")
    if not allowed(view, fn.app):
        raise Denied(f"view '{view}' may not call {qualified}")
    if not fn.read_only and not allow_write:
        raise Denied(f"{qualified} writes; writes are disabled on this hub")
    if fn.handler is None:
        raise Denied(f"{qualified} has no handler")
    return fn.handler(**(args or {}))


def _token_ok(header: str, expected: str) -> bool:
    got = header[7:] if header.lower().startswith("bearer ") else ""
    return bool(expected) and hmac.compare_digest(got.encode(), expected.encode())


def parse_upstreams(spec: str) -> dict[str, str]:
    """``contacts=http://127.0.0.1:8081,contracts=...`` → {app: base_url}."""
    out = {}
    for part in filter(None, (spec or "").split(",")):
        k, _, v = part.partition("=")
        if k and v.startswith(("http://127.0.0.1", "http://localhost", "http://")):
            out[k.strip()] = v.strip().rstrip("/")
    return out


def make_handler(reg: Registry | None = None, token: str | None = None,
                 upstreams: dict[str, str] | None = None, hosts: dict[str, str] | None = None,
                 allow_write: bool = False):
    reg = reg or load_registry()
    token = token if token is not None else os.environ.get("NTXP_HUB_TOKEN", "")
    upstreams = upstreams if upstreams is not None else parse_upstreams(os.environ.get("NTXP_UPSTREAMS", ""))
    hosts = hosts or {a.host: a.name for a in reg.apps.values() if a.host.endswith("ntxpllc.cloud")}

    class H(BaseHTTPRequestHandler):
        server_version = "ntxp-hub"

        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            b = json.dumps(obj, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(b)

        def _host_app(self):
            host = (self.headers.get("Host") or "").split(":")[0].lower()
            return hosts.get(host)

        def _authed(self):
            return _token_ok(self.headers.get("Authorization", ""), token)

        def _view(self):
            return self._host_app() or "all"

        def do_GET(self):
            if self.path.split("?")[0] == "/_ntxp/profile":
                if not self._authed():
                    return self._json({"error": "unauthorized"}, 401)
                return self._json(reg.profile())
            if self.path == "/_ntxp/health":
                return self._json({"ok": True, "apps": sorted(reg.apps)})
            return self._proxy()

        def do_POST(self):
            if self.path.split("?")[0] == "/_ntxp/call":
                if not self._authed():
                    return self._json({"error": "unauthorized"}, 401)
                try:
                    n = int(self.headers.get("Content-Length") or 0)
                    body = json.loads(self.rfile.read(min(n, 1_000_000)) or b"{}")
                    result = dispatch(reg, str(body["function"]), body.get("args") or {},
                                      self._view(), allow_write)
                    return self._json({"result": result})
                except Denied as e:
                    return self._json({"error": str(e)}, 403)
                except KeyError as e:
                    return self._json({"error": f"unknown function {e}"}, 404)
                except (TypeError, ValueError) as e:
                    return self._json({"error": f"bad request: {e}"}, 400)
            return self._proxy()

        do_PATCH = do_DELETE = do_PUT = lambda self: self._proxy()

        def _proxy(self):
            app = self._host_app()
            up = upstreams.get(app or "")
            if not up:
                return self._json({"error": "no view for this host"}, 404)
            n = int(self.headers.get("Content-Length") or 0)
            data = self.rfile.read(n) if n else None
            req = urllib.request.Request(up + self.path, data=data, method=self.command)
            for k, v in self.headers.items():
                if k.lower() not in ("host", "connection", "content-length"):
                    req.add_header(k, v)
            req.add_header("X-Forwarded-Host", self.headers.get("Host", ""))
            try:
                resp = urllib.request.urlopen(req, timeout=30)
            except urllib.error.HTTPError as e:
                resp = e
            except OSError:
                return self._json({"error": "upstream unavailable"}, 502)
            body = resp.read()
            self.send_response(resp.status if hasattr(resp, "status") else resp.code)
            for k, v in resp.headers.items():
                if k.lower() not in ("transfer-encoding", "connection", "content-length"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return H


def serve(host="0.0.0.0", port=8080, **kw):
    ThreadingHTTPServer((host, port), make_handler(**kw)).serve_forever()
