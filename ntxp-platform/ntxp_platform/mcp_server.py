"""One MCP server, scoped by view: exposes every function the view may reach, namespaced
``app__function`` (underscore, MCP-safe), plus ``profile``. Same dispatch path as the hub."""
from __future__ import annotations

import json

from .hub import Denied, dispatch
from .registry import load_registry
from .views import allowed


def build_server(view: str = "all", stateless_http: bool = False):
    from mcp.server.fastmcp import FastMCP
    reg = load_registry()
    mcp = FastMCP(f"ntxp-{view}", stateless_http=stateless_http)

    @mcp.tool()
    def profile() -> str:
        """Combined profile of fields and functions across NTXP apps."""
        p = reg.profile()
        p["apps"] = {k: v for k, v in p["apps"].items() if allowed(view, k)}
        return json.dumps(p)

    @mcp.tool()
    def call(function: str, args: dict | None = None) -> str:
        """Call any registered function by qualified name, e.g. ``links.entity_dossier``."""
        try:
            return json.dumps(dispatch(reg, function, args, view), default=str)
        except Denied as e:
            return json.dumps({"error": str(e)})
        except KeyError:
            return json.dumps({"error": f"unknown function {function}"})
    return mcp
