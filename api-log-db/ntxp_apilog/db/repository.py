"""Thin typed persistence layer over sqlite3.

Holds all SQL. The CLI, MCP server, and HTTP server call these methods; they
never touch SQL directly. Secret fields are encrypted on write and only
decrypted when a caller explicitly asks to ``reveal`` (which is audited).
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..crypto import Cipher, mask
from ..model import ApiEntry, UsageEvent, name_norm

# Secret columns, paired with the in-memory ApiEntry attribute they map to.
_SECRET_COLS = {
    "api_key_enc": "api_key",
    "key_number_enc": "key_number",
    "login_secret_enc": "login_secret",
}


class Repository:
    def __init__(self, conn: sqlite3.Connection, cipher: Cipher | None = None):
        self.conn = conn
        self._cipher = cipher  # shared instance avoids re-reading the key file

    @property
    def cipher(self) -> Cipher:
        if self._cipher is None:
            self._cipher = Cipher()
        return self._cipher

    # -- helpers ------------------------------------------------------------
    def _fts_text(self, e: ApiEntry) -> str:
        parts = [e.name, e.provider, e.category, e.purpose, " ".join(e.tags or [])]
        return " ".join(p for p in parts if p)

    def _rebuild_fts_row(self, api_id: int, e: ApiEntry) -> None:
        self.conn.execute("DELETE FROM apis_fts WHERE api_id = ?", (api_id,))
        self.conn.execute(
            "INSERT INTO apis_fts(api_id, text) VALUES (?, ?)",
            (api_id, self._fts_text(e)),
        )

    # -- write --------------------------------------------------------------
    def upsert_api(self, e: ApiEntry, origin: str = "cli") -> tuple[int, bool]:
        """Create or update an API. ``name_norm`` is the natural merge key.

        Secret fields are only overwritten when the incoming entry supplies a
        (non-None) value, so a metadata-only update never wipes stored keys.
        Returns ``(api_id, is_new)``.
        """
        nn = name_norm(e.name)
        row = self.conn.execute(
            "SELECT api_id FROM apis WHERE name_norm = ? AND is_deleted = 0", (nn,)
        ).fetchone()

        enc = {col: self.cipher.encrypt(getattr(e, attr))
               for col, attr in _SECRET_COLS.items()}
        meta = dict(
            name=e.name, name_norm=nn, provider=e.provider, category=e.category,
            base_url=e.base_url, docs_url=e.docs_url, login_url=e.login_url,
            purpose=e.purpose, auth_type=e.auth_type, login_user=e.login_user,
            cost_model=e.cost_model, currency=e.currency,
            monthly_budget=e.monthly_budget, status=e.status, owner=e.owner,
            tags=json.dumps(e.tags or []), notes=e.notes,
            attrs=json.dumps(e.attrs or {}),
        )

        if row is None:
            cols = list(meta) + list(enc)
            vals = list(meta.values()) + list(enc.values())
            placeholders = ", ".join("?" for _ in cols)
            cur = self.conn.execute(
                f"INSERT INTO apis ({', '.join(cols)}) VALUES ({placeholders})", vals
            )
            api_id = int(cur.lastrowid)
            is_new = True
        else:
            api_id = int(row["api_id"])
            sets, vals = [], []
            for col, val in meta.items():
                sets.append(f"{col} = ?")
                vals.append(val)
            for col, token in enc.items():
                if token is not None:  # only overwrite a secret when one is given
                    sets.append(f"{col} = ?")
                    vals.append(token)
            sets.append("updated_at = datetime('now')")
            vals.append(api_id)
            self.conn.execute(f"UPDATE apis SET {', '.join(sets)} WHERE api_id = ?", vals)
            is_new = False

        self._rebuild_fts_row(api_id, e)
        self.conn.commit()
        return api_id, is_new

    def delete_api(self, api_id: int) -> None:
        """Soft-delete (revocable): keep history, drop from active views/search."""
        self.conn.execute(
            "UPDATE apis SET is_deleted = 1, updated_at = datetime('now') WHERE api_id = ?",
            (api_id,),
        )
        self.conn.execute("DELETE FROM apis_fts WHERE api_id = ?", (api_id,))
        self.conn.commit()

    # -- read ---------------------------------------------------------------
    def _row_to_dict(self, row: sqlite3.Row, reveal: bool) -> dict[str, Any]:
        d = dict(row)
        d["tags"] = json.loads(d.get("tags") or "[]")
        d["attrs"] = json.loads(d.get("attrs") or "{}")
        for col, attr in _SECRET_COLS.items():
            token = d.pop(col, None)
            plain = self.cipher.decrypt(token) if token else None
            d[f"has_{attr}"] = bool(token)
            d[f"{attr}_masked"] = mask(plain) if plain else ""
            if reveal:
                d[attr] = plain
        return d

    def _one(self, where: str, params: tuple, reveal: bool) -> dict[str, Any] | None:
        row = self.conn.execute(
            f"SELECT * FROM apis WHERE {where} AND is_deleted = 0", params
        ).fetchone()
        if not row:
            return None
        d = self._row_to_dict(row, reveal)
        self._attach_spend([d])
        return d

    def get_api(self, api_id: int, reveal: bool = False) -> dict[str, Any] | None:
        return self._one("api_id = ?", (api_id,), reveal)

    def find_by_name(self, name: str, reveal: bool = False) -> dict[str, Any] | None:
        return self._one("name_norm = ?", (name_norm(name),), reveal)

    def resolve(self, name_or_id: str | int, reveal: bool = False) -> dict[str, Any] | None:
        """Look up by api_id (int or digit-string) or by name."""
        if isinstance(name_or_id, int) or str(name_or_id).isdigit():
            return self.get_api(int(name_or_id), reveal)
        return self.find_by_name(str(name_or_id), reveal)

    def list_apis(self, status: str | None = None, category: str | None = None,
                  limit: int = 500) -> list[dict[str, Any]]:
        sql = "SELECT * FROM apis WHERE is_deleted = 0"
        params: list[Any] = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY name COLLATE NOCASE LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        out = [self._row_to_dict(r, reveal=False) for r in rows]
        self._attach_spend(out)
        return out

    def search(self, query: str, limit: int = 25) -> list[dict[str, Any]]:
        """Full-text search over name/provider/purpose/tags/category.

        Falls back to a LIKE scan if the query has no usable FTS tokens.
        """
        q = (query or "").strip()
        rows: list[sqlite3.Row] = []
        if q:
            try:
                fts_q = " ".join(f'"{t}"*' for t in q.split())
                rows = self.conn.execute(
                    "SELECT a.* FROM apis_fts f JOIN apis a ON a.api_id = f.api_id "
                    "WHERE apis_fts MATCH ? AND a.is_deleted = 0 LIMIT ?",
                    (fts_q, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = []
        if not rows:
            like = f"%{q}%"
            rows = self.conn.execute(
                "SELECT * FROM apis WHERE is_deleted = 0 AND ("
                "name LIKE ? OR provider LIKE ? OR purpose LIKE ? OR category LIKE ?"
                ") ORDER BY name COLLATE NOCASE LIMIT ?",
                (like, like, like, like, limit),
            ).fetchall()
        out = [self._row_to_dict(r, reveal=False) for r in rows]
        self._attach_spend(out)
        return out

    def _attach_spend(self, rows: list[dict[str, Any]]) -> None:
        """Annotate each row with its lifetime spend (single grouped query)."""
        if not rows:
            return
        spend = {
            r["api_id"]: r["total"]
            for r in self.conn.execute(
                "SELECT api_id, COALESCE(SUM(cost), 0) AS total FROM usage_log GROUP BY api_id"
            ).fetchall()
        }
        for r in rows:
            r["spend_total"] = round(spend.get(r["api_id"], 0.0), 4)

    # -- usage / cost -------------------------------------------------------
    def log_usage(self, ev: UsageEvent) -> int:
        cur = self.conn.execute(
            "INSERT INTO usage_log(api_id, cost, currency, units, unit_kind, "
            "description, requested_by, origin) VALUES (?,?,?,?,?,?,?,?)",
            (ev.api_id, ev.cost, ev.currency, ev.units, ev.unit_kind,
             ev.description, ev.requested_by, ev.origin),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def log_access(self, api_id: int, action: str, accessor: str | None = None,
                   purpose: str | None = None, origin: str = "cli") -> None:
        self.conn.execute(
            "INSERT INTO access_log(api_id, action, accessor, purpose, origin) "
            "VALUES (?,?,?,?,?)",
            (api_id, action, accessor, purpose, origin),
        )
        self.conn.commit()

    # -- analytics ----------------------------------------------------------
    def stats(self) -> dict[str, Any]:
        c = self.conn
        total_apis = c.execute("SELECT COUNT(*) AS n FROM apis WHERE is_deleted = 0").fetchone()["n"]
        by_status = {r["status"]: r["n"] for r in c.execute(
            "SELECT status, COUNT(*) AS n FROM apis WHERE is_deleted = 0 GROUP BY status"
        ).fetchall()}
        by_category = {r["category"] or "uncategorized": r["n"] for r in c.execute(
            "SELECT category, COUNT(*) AS n FROM apis WHERE is_deleted = 0 GROUP BY category"
        ).fetchall()}
        total_spend = c.execute("SELECT COALESCE(SUM(cost), 0) AS s FROM usage_log").fetchone()["s"]
        spend_by_api = [
            {"name": r["name"], "spend": round(r["s"], 4)}
            for r in c.execute(
                "SELECT a.name, COALESCE(SUM(u.cost), 0) AS s FROM apis a "
                "LEFT JOIN usage_log u ON u.api_id = a.api_id "
                "WHERE a.is_deleted = 0 GROUP BY a.api_id ORDER BY s DESC LIMIT 20"
            ).fetchall()
        ]
        spend_by_month = [
            {"month": r["m"], "spend": round(r["s"], 4)}
            for r in c.execute(
                "SELECT substr(occurred_at, 1, 7) AS m, SUM(cost) AS s "
                "FROM usage_log GROUP BY m ORDER BY m DESC LIMIT 12"
            ).fetchall()
        ]
        return {
            "total_apis": total_apis,
            "by_status": by_status,
            "by_category": by_category,
            "total_spend": round(total_spend, 4),
            "spend_by_api": spend_by_api,
            "spend_by_month": spend_by_month,
        }
