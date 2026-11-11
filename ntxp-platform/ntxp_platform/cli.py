from __future__ import annotations

import argparse
import json
import sys

from .hub import Denied, dispatch, serve
from .registry import load_registry


def main(argv=None) -> int:
    p = argparse.ArgumentParser("ntxp-platform")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("profile")
    c = sub.add_parser("call")
    c.add_argument("function"); c.add_argument("args", nargs="?", default="{}")
    c.add_argument("--view", default="all")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8080); s.add_argument("--host", default="0.0.0.0")
    m = sub.add_parser("mcp"); m.add_argument("--view", default="all")
    a = p.parse_args(argv)
    reg = load_registry()
    if a.cmd == "profile":
        print(json.dumps(reg.profile(), indent=2)); return 0
    if a.cmd == "call":
        try:
            print(json.dumps(dispatch(reg, a.function, json.loads(a.args), a.view), default=str, indent=2))
        except (Denied, KeyError) as e:
            print(f"error: {e}", file=sys.stderr); return 2
        return 0
    if a.cmd == "serve":
        serve(a.host, a.port); return 0
    if a.cmd == "mcp":
        from .mcp_server import build_server
        build_server(a.view).run(); return 0
    return 1
