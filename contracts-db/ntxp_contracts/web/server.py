"""Zero-dependency web server for the contract dashboard + profile screens.

Built on the standard library only (``http.server`` + threading), so it runs
anywhere the package installs with no extra deps. WAL-mode SQLite plus
field-level PATCH gives concurrent editors safe, conflict-light saves; the
dashboard polls ``/api/changes`` to surface each other's saves live.

Routes
  GET   /                       dashboard (inline-editable contract log)
  GET   /contract?id=<id>       single-contract profile screen
  GET   /static/<file>          css / js
  GET   /assets/<file>          NTXP logo / favicon from NTXP_ASSETS_DIR (the Document Engine's own files;
                                proprietary, mounted at deploy time, never in git)
  GET   /api/branding           resolved brand (scanned from Claude settings)
  GET   /api/meta               types, scope vocab, poll interval, latest_seq
  GET   /api/contracts          list all contracts
  POST  /api/contracts          create a blank contract -> {contract}
  GET   /api/contracts/<id>     full profile (contract + owner + jobs + totals)
  PATCH /api/contracts/<id>     {field,value,rev?,actor?} instant save -> {contract}
  DELETE/api/contracts/<id>     soft delete
  POST  /api/contracts/<id>/jobs   sync job rows for the profile roll-up
  GET   /api/contracts/<id>/vcard  owner-entity vCard download (.vcf)
  GET   /api/contracts/<id>/ics    expiration calendar event (.ics)
  GET   /api/changes?since=<seq>   live-poll delta probe
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import hmac
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .. import branding, contactfile, jobs as jobs_mod
from ..config import CONTRACT_TYPES, SCOPE_VOCAB, WEB_HOST, WEB_POLL_MS, WEB_PORT
from ..db import connect, migrate
from ..db.repository import ConflictError, Repository

STATIC = Path(__file__).parent / "static"
MAX_BODY = 1_048_576
_LOOPBACK = {"127.0.0.1", "localhost", "::1", "[::1]"}


def _allowed_hosts() -> set[str]:
    """Host names this server answers to. Anything else (DNS rebinding) is refused."""
    extra = {h.strip().lower() for h in os.environ.get("NTXP_CONTRACTS_ALLOWED_HOSTS", "").split(",") if h.strip()}
    return {h.lower() for h in _LOOPBACK} | extra


def _api_token() -> str:
    return os.environ.get("NTXP_CONTRACTS_TOKEN", "")
_ASSET_TYPES = {".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon"}


# Migrations are applied once per process (at serve() startup); the schema does
# not change between requests, so re-globbing the migrations dir and opening a
# write transaction on every request (incl. each poll) would be pure hot-path
# waste. _repo() therefore just connects.
_MIGRATED: set[str] = set()


def _ensure_migrated(db_override):
    key = str(db_override or "")
    if key not in _MIGRATED:
        conn = connect(db_override)
        migrate(conn)
        conn.close()
        _MIGRATED.add(key)


def _repo(db_override):
    conn = connect(db_override)
    return Repository(conn), conn


class _Bad(Exception):
    def __init__(self, code: int, msg: str):
        self.code, self.msg = code, msg


def make_handler(db_override):
    class Handler(BaseHTTPRequestHandler):
        server_version = "NTXPContracts/0.1"

        # -- helpers --------------------------------------------------------
        def _json(self, obj, status=200):
            body = json.dumps(obj, default=str, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_bytes(self, data: bytes, ctype: str, download: str | None = None):
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            if download:
                self.send_header("Content-Disposition",
                                 f'attachment; filename="{download}"')
            self.end_headers()
            self.wfile.write(data)

        def _file(self, path: Path, ctype: str, download: str | None = None):
            self._send_bytes(path.read_bytes(), ctype, download)

        def _raw(self, text: str, ctype: str, download: str | None = None):
            self._send_bytes(text.encode("utf-8"), ctype, download)

        def _body_json(self) -> dict:
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                raise _Bad(400, "bad Content-Length")
            if n < 0:
                raise _Bad(400, "bad Content-Length")
            if n > MAX_BODY:
                raise _Bad(413, "request body too large")
            if not n:
                return {}
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except Exception:
                raise _Bad(400, "invalid JSON")
            if not isinstance(body, dict):
                raise _Bad(400, "JSON object required")
            return body

        def log_message(self, *a):  # quiet
            pass

        # Every request is migrated-once then run inside a guard so a missing
        # asset, branding I/O error, or unexpected exception returns a clean
        # 500 instead of tearing down the connection with a stack trace.
        def _refuse(self):
            """CSRF / DNS-rebinding / token gate. Returns True (after replying) when the request must stop."""
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].lower() if not (self.headers.get("Host") or "").startswith("[") \
                else (self.headers.get("Host") or "").split("]")[0] + "]"
            if host not in _allowed_hosts():
                self._json({"error": "host not allowed"}, 421)
                return True
            writes = self.command in ("POST", "PATCH", "DELETE")
            if writes:
                origin = self.headers.get("Origin")
                if origin and origin.split("://", 1)[-1].lower() != (self.headers.get("Host") or "").lower():
                    self._json({"error": "cross-origin write refused"}, 403)
                    return True
                if self.command in ("POST", "PATCH") and \
                        (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
                    self._json({"error": "Content-Type: application/json required"}, 415)
                    return True
            tok = _api_token()
            if tok and urlparse(self.path).path.startswith("/api/"):
                got = (self.headers.get("Authorization") or "")[7:].strip()
                if not hmac.compare_digest(got.encode(), tok.encode()):
                    self._json({"error": "unauthorized"}, 401)
                    return True
            return False

        def _guard(self, fn):
            try:
                if self._refuse():
                    return
                _ensure_migrated(db_override)
                fn()
            except BrokenPipeError:
                pass
            except _Bad as e:
                try:
                    self._json({"error": e.msg}, e.code)
                except Exception:
                    pass
            except Exception:  # noqa: BLE001 — last-resort request guard
                import logging
                logging.getLogger(__name__).exception("request failed")
                try:
                    self._json({"error": "server error"}, 500)
                except Exception:
                    pass

        def do_GET(self):
            self._guard(self._get)

        def do_POST(self):
            self._guard(self._post)

        def do_PATCH(self):
            self._guard(self._patch)

        def do_DELETE(self):
            self._guard(self._delete)

        # -- GET ------------------------------------------------------------
        def _get(self):
            u = urlparse(self.path)
            path, qs = u.path, parse_qs(u.query)
            if path == "/" or path == "/index.html":
                return self._file(STATIC / "dashboard.html", "text/html; charset=utf-8")
            if path == "/contract":
                return self._file(STATIC / "contract.html", "text/html; charset=utf-8")
            if path.startswith("/assets/"):
                name = path[len("/assets/"):]
                base = os.environ.get("NTXP_ASSETS_DIR")
                ext = os.path.splitext(name)[1].lower()
                f = Path(base) / name if base else None
                if (not f or not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or ext not in _ASSET_TYPES
                        or not f.is_file()):
                    return self._json({"error": "not found"}, 404)
                return self._file(f, _ASSET_TYPES[ext])
            if path.startswith("/static/"):
                f = STATIC / path[len("/static/"):]
                if f.is_file() and STATIC in f.resolve().parents:
                    ct = "text/css" if f.suffix == ".css" else (
                        "application/javascript" if f.suffix == ".js" else "text/plain")
                    return self._file(f, ct + "; charset=utf-8")
                return self._json({"error": "not found"}, 404)

            if path == "/api/branding":
                return self._json(branding.resolve_brand().to_dict())
            if path == "/api/meta":
                repo, conn = _repo(db_override)
                try:
                    meta = {
                        "contract_types": list(CONTRACT_TYPES),
                        "scope_vocab": list(SCOPE_VOCAB),
                        "poll_ms": WEB_POLL_MS,
                        "latest_seq": repo.changes_since(0)["latest_seq"],
                        "stats": repo.stats(),
                    }
                finally:
                    conn.close()
                return self._json(meta)
            if path == "/api/contracts":
                repo, conn = _repo(db_override)
                try:
                    return self._json({"contracts": repo.list_contracts(),
                                       "latest_seq": repo.changes_since(0)["latest_seq"]})
                finally:
                    conn.close()
            if path == "/api/changes":
                try:
                    since = int((qs.get("since") or ["0"])[0])
                except ValueError:
                    return self._json({"error": "since must be an integer"}, 400)
                repo, conn = _repo(db_override)
                try:
                    return self._json(repo.changes_since(since))
                finally:
                    conn.close()

            m = re.match(r"^/api/contracts/(\d+)(?:/(\w+))?$", path)
            if m:
                cid, sub = int(m.group(1)), m.group(2)
                repo, conn = _repo(db_override)
                try:
                    if sub == "vcard":
                        prof = repo.get_profile(cid)
                        if not prof:
                            return self._json({"error": "not found"}, 404)
                        owner = (prof or {}).get("owner") or {
                            "name": (prof or {}).get("contract", {}).get("owner_entity")}
                        return self._raw(contactfile.vcard(owner),
                                         "text/vcard; charset=utf-8", "owner-contact.vcf")
                    if sub == "ics":
                        c = repo.get_contract(cid)
                        ics = contactfile.ics_expiration(c) if c else None
                        if not ics:
                            return self._json({"error": "no expiration date"}, 404)
                        return self._raw(ics, "text/calendar; charset=utf-8",
                                         "contract-expiration.ics")
                    prof = repo.get_profile(cid)
                    if not prof:
                        return self._json({"error": "not found"}, 404)
                    return self._json(prof)
                finally:
                    conn.close()
            return self._json({"error": "not found"}, 404)

        # -- POST -----------------------------------------------------------
        def _post(self):
            u = urlparse(self.path)
            if u.path == "/api/contracts":
                body = self._body_json()
                repo, conn = _repo(db_override)
                try:
                    c = repo.create_contract(
                        title=body.get("contract_title") or "Untitled Contract",
                        actor=body.get("actor") or "web")
                    return self._json({"contract": c}, 201)
                finally:
                    conn.close()
            m = re.match(r"^/api/contracts/(\d+)/jobs$", u.path)
            if m:
                cid = int(m.group(1))
                body = self._body_json()
                rows = body.get("jobs") or []
                repo, conn = _repo(db_override)
                try:
                    c = repo.get_contract(cid)
                    default_no = c["contract_no"] if c else None
                    summary = jobs_mod.sync_jobs(repo, rows, default_no)
                    return self._json({"ok": True, **summary})
                finally:
                    conn.close()
            return self._json({"error": "not found"}, 404)

        # -- PATCH ----------------------------------------------------------
        def _patch(self):
            m = re.match(r"^/api/contracts/(\d+)$", urlparse(self.path).path)
            if not m:
                return self._json({"error": "not found"}, 404)
            cid = int(m.group(1))
            body = self._body_json()
            field = body.get("field")
            repo, conn = _repo(db_override)
            try:
                updated = repo.update_field(
                    cid, field, body.get("value"),
                    actor=body.get("actor") or "web",
                    expected_rev=body.get("rev"))
                return self._json({"contract": updated})
            except ConflictError as e:
                return self._json({"error": "conflict", "contract": e.args[0]}, 409)
            except (ValueError, KeyError, sqlite3.IntegrityError) as e:
                return self._json({"error": str(e)}, 400)
            finally:
                conn.close()

        # -- DELETE ---------------------------------------------------------
        def _delete(self):
            m = re.match(r"^/api/contracts/(\d+)$", urlparse(self.path).path)
            if not m:
                return self._json({"error": "not found"}, 404)
            repo, conn = _repo(db_override)
            try:
                repo.soft_delete(int(m.group(1)))
                return self._json({"ok": True})
            finally:
                conn.close()

    return Handler


def serve(db_override: str | None = None, host: str | None = None,
          port: int | None = None) -> None:
    host = host or WEB_HOST
    port = port or WEB_PORT
    if host not in _LOOPBACK and not _api_token():
        raise SystemExit("Refusing to bind a writable, unauthenticated contracts API to a non-loopback address. "
                         "Set NTXP_CONTRACTS_TOKEN (Bearer token required on /api) or bind 127.0.0.1 behind an "
                         "authenticating proxy, and list the public host in NTXP_CONTRACTS_ALLOWED_HOSTS.")
    # Apply migrations once, before the first request.
    _ensure_migrated(db_override)
    httpd = ThreadingHTTPServer((host, port), make_handler(db_override))
    print(f"NTXP Contracts dashboard → http://{host}:{port}/  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
        httpd.server_close()
