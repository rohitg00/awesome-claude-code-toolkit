"""Google OAuth login for the dashboard.

Gating the dashboard behind Google sign-in is what makes it safe to share
beyond loopback: only allow-listed Google accounts (by email or hosted domain)
can reach the registry and its credentials.

**Off by default.** If `NTXP_APILOG_GOOGLE_CLIENT_ID` / `_SECRET` are unset, the
dashboard runs exactly as before (loopback, no login). Set them — and an
allowlist — to require Google sign-in.

Flow: the standard OAuth 2.0 authorization-code flow. We exchange the code with
Google over TLS (a trusted channel) and read the userinfo endpoint, so no local
JWT-signature verification is needed. Sessions are random opaque tokens held in
memory and referenced by an HttpOnly cookie.

| Env var | Purpose |
|---|---|
| `NTXP_APILOG_GOOGLE_CLIENT_ID` | OAuth client id (enables login when set) |
| `NTXP_APILOG_GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `NTXP_APILOG_OAUTH_REDIRECT` | Redirect URI (default `http://<host>:<port>/auth/callback`) |
| `NTXP_APILOG_ALLOWED_EMAILS` | Comma-separated allowed emails |
| `NTXP_APILOG_ALLOWED_DOMAIN` | Allowed hosted domain (e.g. `ntxp.com`) |
"""
from __future__ import annotations

import json
import os
import secrets
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
SCOPES = "openid email profile"

SESSION_COOKIE = "ntxp_session"
SESSION_TTL = 12 * 3600          # 12 hours
STATE_TTL = 600                  # 10 minutes to complete the round-trip


@dataclass
class OAuthConfig:
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    allowed_emails: set[str] = field(default_factory=set)
    allowed_domain: str = ""

    @classmethod
    def from_env(cls, host: str, port: int) -> "OAuthConfig":
        env = os.environ.get
        default_redirect = f"http://{host}:{port}/auth/callback"
        emails = {e.strip().lower() for e in (env("NTXP_APILOG_ALLOWED_EMAILS") or "").split(",") if e.strip()}
        return cls(
            client_id=env("NTXP_APILOG_GOOGLE_CLIENT_ID") or "",
            client_secret=env("NTXP_APILOG_GOOGLE_CLIENT_SECRET") or "",
            redirect_uri=env("NTXP_APILOG_OAUTH_REDIRECT") or default_redirect,
            allowed_emails=emails,
            allowed_domain=(env("NTXP_APILOG_ALLOWED_DOMAIN") or "").strip().lower(),
        )

    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def is_allowed(self, email: str | None) -> bool:
        """An account is allowed if it matches the email allowlist or domain.

        If neither allowlist is configured, any Google account that signs in is
        accepted — surfaced as a warning at startup so it isn't a silent default.
        """
        if not email:
            return False
        email = email.lower()
        if not self.allowed_emails and not self.allowed_domain:
            return True
        if email in self.allowed_emails:
            return True
        if self.allowed_domain and email.endswith("@" + self.allowed_domain):
            return True
        return False


class SessionStore:
    """In-memory session + OAuth-state store (single-process dashboard)."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}
        self._states: dict[str, float] = {}

    # -- OAuth state (CSRF) --------------------------------------------------
    def new_state(self) -> str:
        self._sweep()
        s = secrets.token_urlsafe(24)
        self._states[s] = time.time() + STATE_TTL
        return s

    def consume_state(self, state: str | None) -> bool:
        if not state:
            return False
        exp = self._states.pop(state, None)
        return exp is not None and exp > time.time()

    # -- sessions ------------------------------------------------------------
    def create(self, email: str, name: str) -> str:
        self._sweep()
        sid = secrets.token_urlsafe(32)
        self._sessions[sid] = {"email": email, "name": name, "exp": time.time() + SESSION_TTL}
        return sid

    def get(self, sid: str | None) -> dict | None:
        if not sid:
            return None
        sess = self._sessions.get(sid)
        if sess and sess["exp"] > time.time():
            return sess
        self._sessions.pop(sid, None)
        return None

    def destroy(self, sid: str | None) -> None:
        if sid:
            self._sessions.pop(sid, None)

    def _sweep(self) -> None:
        now = time.time()
        self._states = {k: v for k, v in self._states.items() if v > now}
        self._sessions = {k: v for k, v in self._sessions.items() if v["exp"] > now}


def authorize_url(cfg: OAuthConfig, state: str) -> str:
    params = {
        "client_id": cfg.client_id,
        "redirect_uri": cfg.redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)


def _post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _get_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def exchange_code(cfg: OAuthConfig, code: str) -> dict:
    """Trade an auth code for tokens (over TLS) and return Google's userinfo."""
    tokens = _post_form(TOKEN_URL, {
        "code": code,
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "redirect_uri": cfg.redirect_uri,
        "grant_type": "authorization_code",
    })
    access_token = tokens.get("access_token")
    if not access_token:
        raise ValueError("Google token exchange returned no access_token")
    return _get_json(USERINFO_URL, access_token)
