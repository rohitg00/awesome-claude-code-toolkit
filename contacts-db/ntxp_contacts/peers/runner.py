"""One cycle of the peer machinery: pull (contracts) -> emit -> deliver -> housekeeping.
Run from `ntxp peers run --watch`, or the background thread in `ntxp serve-http`."""
from __future__ import annotations

import logging
import os
import threading
import time

from . import contracts as contracts_mod
from . import context as ctx
from .events import deliver_due, emit_changes, outbox_stats
from .registry import load_peers

log = logging.getLogger("ntxp.peers")
RETAIN_SEEN_S = 30 * 86400
RETAIN_DELIVERED_S = 14 * 86400


def run_cycle(conn, deliver: bool = True, pull: bool = True, post=None) -> dict:
    peers, errors = load_peers()
    out = {"errors": errors, "pull": {}, "emit": {}, "deliver": {}}
    if pull:
        for name, peer in peers.items():
            if peer.pulls:
                try:
                    out["pull"][name] = contracts_mod.pull(conn, peer)
                except Exception as exc:                      # a down peer must not stop the others
                    conn.rollback()
                    out["pull"][name] = {"error": f"{type(exc).__name__}: {exc}"[:200]}
    out["emit"] = emit_changes(conn, peers)
    if deliver:
        kw = {"post": post} if post else {}
        out["deliver"] = deliver_due(conn, peers, **kw)
    conn.execute("DELETE FROM peer_seen WHERE seen_at < ?", (ctx.now_ts(conn, -RETAIN_SEEN_S),))
    conn.execute("DELETE FROM peer_outbox WHERE status='delivered' AND delivered_at < ?",
                 (ctx.now_ts(conn, -RETAIN_DELIVERED_S),))
    conn.commit()
    out["outbox"] = outbox_stats(conn)
    return out


def start_background(db_override=None, interval: float | None = None) -> threading.Thread | None:
    """Daemon thread running run_cycle every NTXP_PEERS_INTERVAL seconds (default 30) when peers
    are configured. Disable with NTXP_PEERS_AUTORUN=0 (e.g. when cron runs `ntxp peers run`)."""
    if os.environ.get("NTXP_PEERS_AUTORUN", "1") == "0" or not load_peers()[0]:
        return None
    every = interval or float(os.environ.get("NTXP_PEERS_INTERVAL", "30"))

    def loop():
        from ..db import connect, migrate
        while True:
            try:
                conn = connect(db_override)
                try:
                    migrate(conn)
                    run_cycle(conn)
                finally:
                    conn.close()
            except Exception:
                log.exception("peer cycle failed")
            time.sleep(every)

    t = threading.Thread(target=loop, name="ntxp-peers", daemon=True)
    t.start()
    return t
