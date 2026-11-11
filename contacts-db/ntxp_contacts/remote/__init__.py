"""Cloud-hosted, stateless MCP 2.0 surface + OAuth-token gate + location links.

Importing this module does NOT require the `mcp` package; only
build_http_app()/serve() do (they pull in FastMCP lazily), so auth and maps
helpers stay testable without the server stack installed.
"""
from .maps import maps_link, apple_maps_link
from .auth import verify_token

__all__ = ["maps_link", "apple_maps_link", "verify_token", "build_http_app", "serve"]


def build_http_app(db_override=None):
    from .http_server import build_http_app as _b
    return _b(db_override)


def serve(db_override=None, host: str = "0.0.0.0", port: int = 8080):
    from .http_server import serve as _s
    return _s(db_override, host, port)
