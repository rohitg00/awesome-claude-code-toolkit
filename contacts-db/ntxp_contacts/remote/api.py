"""REST API behind the live contacts page and the Google Sheet mirror.

Pure functions (`handle`) over a DB connection + an authenticated user, so the
logic is unit-testable without the HTTP stack; `ApiApp` is the thin ASGI shell.
Every endpoint serves **exposed** contacts only (the grader's gate) — the same
rule as the iOS feed — and every write is logged to `change_log` with the editor's
email so it fans out through the normal sync pipeline.

    GET   /api/me
    GET   /api/contacts?q=&company=&role=&trade=&city=&state=&project=&label=
                       &near=Dallas,TX&miles=30&sort=&dir=&limit=&offset=
    GET   /api/facets[?field=company&q=va&limit=25]
    PATCH /api/contacts/<id>            {"field": "value", ...}   (inline edit)
    POST  /api/contacts/<id>/labels     {"add": [...], "remove": [...]}
    GET   /api/report?type=directory|full|trade|company|label&<filters>   -> doc-engine spec
    GET   /api/export.csv?<filters>
    GET   /api/council                  persisted council answers + effectiveness
"""
from __future__ import annotations

import csv
import io
import json
import re
from urllib.parse import parse_qs

from .. import normalize as N
from ..geo import miles_between, parse_place, coords

TAG_LABEL_KINDS = ("label", "member", "cjp", "event", "certification", "domain", "project")
SORTS = {
    "name": "LOWER(COALESCE(last_name,'')), LOWER(COALESCE(first_name,''))",
    "company": "LOWER(COALESCE(company,''))", "role": "LOWER(COALESCE(role,''))",
    "trade": "LOWER(COALESCE(trade,''))", "city": "LOWER(COALESCE(city,''))",
    "state": "COALESCE(state,'')", "phone": "COALESCE(phone,'')",
    "email": "LOWER(COALESCE(email,''))", "project": "LOWER(COALESCE(project,''))",
    "grade": "COALESCE(grade,0)",
}
EXACT = {"company", "role", "trade", "city", "state", "project"}
EDITABLE = {"first_name", "last_name", "title", "email", "phone", "linkedin_url",
            "photo_url", "company", "city", "state", "role", "trade", "project"}
MAX_LEN = 300

_TAGSUB = (
    "(SELECT t.value FROM entity_tags et JOIN tags t ON t.tag_id=et.tag_id "
    "WHERE t.kind='{kind}' AND ((et.entity_type='contact' AND et.entity_id=c.contact_id) "
    "OR (et.entity_type='org' AND et.entity_id=c.org_id)) ORDER BY t.tag_id LIMIT 1)")
_MULTI = (
    "(SELECT GROUP_CONCAT(t.value, '|') FROM entity_tags et JOIN tags t ON t.tag_id=et.tag_id "
    "WHERE t.kind='{kind}' AND ((et.entity_type='contact' AND et.entity_id=c.contact_id) "
    "OR (et.entity_type='org' AND et.entity_id=c.org_id)))")
_LABELS = (
    "(SELECT GROUP_CONCAT(t.value, '|') FROM entity_tags et JOIN tags t ON t.tag_id=et.tag_id "
    "WHERE t.kind IN ({kinds}) AND ((et.entity_type='contact' AND et.entity_id=c.contact_id) "
    "OR (et.entity_type='org' AND et.entity_id=c.org_id)))")


def _addr(col: str) -> str:
    return ("(SELECT a." + col + " FROM addresses a WHERE (a.contact_id=c.contact_id OR "
            "a.org_id=c.org_id) AND a." + col + " IS NOT NULL "
            "ORDER BY (CASE WHEN a.contact_id IS NULL THEN 1 ELSE 0 END), a.address_id LIMIT 1)")


BASE = (
    "SELECT c.contact_id AS id, c.first_name AS first_name, c.last_name AS last_name, "
    "c.full_name AS full_name, c.title AS title, c.photo_url AS photo_url, "
    "c.linkedin_url AS linkedin_url, c.updated_at AS updated_at, o.name AS company, "
    "o.website AS website, "
    "(SELECT e.email FROM emails e WHERE e.contact_id=c.contact_id AND e.is_invalid=0 "
    "ORDER BY e.is_primary DESC, e.email_id LIMIT 1) AS email, "
    "(SELECT COALESCE(p.phone_e164, p.phone_raw) FROM phones p WHERE p.contact_id=c.contact_id "
    "ORDER BY p.phone_id LIMIT 1) AS phone, "
    + _addr("city") + " AS city, " + _addr("state") + " AS state, "
    + _TAGSUB.format(kind="role") + " AS role, "
    + _TAGSUB.format(kind="trade") + " AS trade, "
    + _TAGSUB.format(kind="project") + " AS project, "
    + _MULTI.format(kind="project") + " AS projects, "
    + _LABELS.format(kinds=",".join("'%s'" % k for k in TAG_LABEL_KINDS)) + " AS labels, "
    "g.grade AS grade, g.grade_band AS grade_band "
    "FROM contacts c LEFT JOIN organizations o ON o.org_id=c.org_id "
    "LEFT JOIN contact_grade g ON g.contact_id=c.contact_id "
    "WHERE c.is_deleted=0 AND (g.is_exposed IS NULL OR g.is_exposed=1)")


class ApiError(Exception):
    def __init__(self, status: int, msg: str):
        super().__init__(msg)
        self.status, self.msg = status, msg


def _q1(query: dict, key: str, default: str = "") -> str:
    v = query.get(key, default)
    if isinstance(v, list):
        v = v[0] if v else default
    return (v or "").strip()


def _qall(query: dict, key: str) -> list[str]:
    v = query.get(key)
    if v is None:
        return []
    vals = v if isinstance(v, list) else [v]
    return [x.strip() for x in vals if x and x.strip()][:50]


def _filters(query: dict):
    """-> (WHERE sql, params, proximity (lat,lng,miles)|None). A repeated key is
    an OR within that field (a checklist); different fields AND together."""
    where, params = [], []
    for f in EXACT:
        vals = [v.lower() for v in _qall(query, f)]
        if not vals:
            continue
        if f == "project":     # a contact can be on several projects: match ANY of them
            where.append("(" + " OR ".join("LOWER('|'||COALESCE(projects,'')||'|') LIKE ?" for _ in vals) + ")")
            params += [f"%|{v}|%" for v in vals]
        else:
            where.append(f"LOWER(COALESCE({f},'')) IN ({','.join('?' * len(vals))})")
            params += vals
    labels = [v.lower() for v in _qall(query, "label")]
    if labels:
        ors = []
        for l in labels:
            ors.append("(LOWER('|'||COALESCE(labels,'')||'|') LIKE ? OR LOWER(COALESCE(company,'')) = ?)")
            params += [f"%|{l}|%", l]
        where.append("(" + " OR ".join(ors) + ")")
    q = _q1(query, "q")
    if q:
        for tok in q.lower().split()[:6]:
            where.append("LOWER(COALESCE(full_name,'')||' '||COALESCE(company,'')||' '||"
                         "COALESCE(email,'')||' '||COALESCE(title,'')||' '||COALESCE(project,'')||' '||"
                         "COALESCE(trade,'')||' '||COALESCE(role,'')||' '||COALESCE(labels,'')) LIKE ?")
            params.append(f"%{tok}%")
    prox = None
    near, miles = _q1(query, "near"), _q1(query, "miles")
    if near and miles:
        pt = parse_place(near)
        if pt is None:
            raise ApiError(400, f"unknown place '{near}' for proximity (city-level, TX/OK region)")
        try:
            prox = (pt[0], pt[1], float(miles))
        except ValueError:
            raise ApiError(400, "miles must be a number")
    return (" WHERE " + " AND ".join(where)) if where else "", params, prox


def _rows(conn, query: dict, limit: int | None, offset: int = 0):
    where, params, prox = _filters(query)
    sort = SORTS.get(_q1(query, "sort"), SORTS["name"])
    direction = "DESC" if _q1(query, "dir").lower() == "desc" else "ASC"
    order = ", ".join(f"{part.strip()} {direction}" for part in _split_order(sort))
    sql = f"SELECT * FROM ({BASE}) x{where} ORDER BY {order}, id"
    if prox is None:
        total = conn.execute(f"SELECT COUNT(*) FROM ({BASE}) x{where}", params).fetchone()[0]
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params = params + [limit, offset]
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    else:
        lat, lng, mi = prox
        out = []
        for r in conn.execute(sql, params).fetchall():
            d = dict(r)
            pt = coords(d.get("city"), d.get("state"))
            if pt and miles_between((lat, lng), pt) <= mi:
                d["miles"] = round(miles_between((lat, lng), pt), 1)
                out.append(d)
        total = len(out)
        rows = out[offset:offset + limit] if limit is not None else out
    return total, [_shape(r) for r in rows]


def _split_order(sort: str):
    # SORTS values contain commas only between top-level terms (no function commas
    # except inside COALESCE(...,'') which we protect by depth).
    parts, depth, cur = [], 0, ""
    for ch in sort:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def _shape(r: dict) -> dict:
    labels = [x for x in (r.get("labels") or "").split("|") if x]
    r["labels"] = sorted(set(labels))
    r["updated_at"] = str(r.get("updated_at"))
    em = r.get("email") or ""
    r["domain"] = em.rsplit("@", 1)[1] if "@" in em else None
    return r


# -- endpoints ---------------------------------------------------------------

def _facets(conn, query: dict) -> dict:
    field = _q1(query, "field")
    if field:
        if field not in EXACT:
            raise ApiError(400, "unknown facet field")
        q = _q1(query, "q").lower()
        lim = min(int(_q1(query, "limit", "25") or 25), 200)
        if field == "project":
            seen: dict[str, int] = {}
            for r in conn.execute(f"SELECT projects FROM ({BASE}) x WHERE projects IS NOT NULL").fetchall():
                for v in set((r["projects"] or "").split("|")):
                    if v and (not q or q in v.lower()):
                        seen[v] = seen.get(v, 0) + 1
            top = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))[:lim]
            return {"field": field, "values": [{"value": k, "count": n} for k, n in top]}
        sql = (f"SELECT {field} AS v, COUNT(*) AS n FROM ({BASE}) x WHERE {field} IS NOT NULL "
               f"AND {field} <> ''" + (f" AND LOWER({field}) LIKE ?" if q else "")
               + f" GROUP BY {field} ORDER BY n DESC, v LIMIT ?")
        params = ([f"%{q}%"] if q else []) + [lim]
        return {"field": field, "values": [{"value": r["v"], "count": r["n"]}
                                           for r in conn.execute(sql, params).fetchall()]}
    out = {}
    out["project"] = [x["value"] for x in _facets(conn, {"field": "project", "limit": "500"})["values"]]
    for f in ("role", "trade", "state"):
        out[f] = [r["v"] for r in conn.execute(
            f"SELECT DISTINCT {f} AS v FROM ({BASE}) x WHERE {f} IS NOT NULL AND {f} <> '' "
            f"ORDER BY v LIMIT 500").fetchall()]
    lab: dict[str, int] = {}
    for r in conn.execute(f"SELECT labels FROM ({BASE}) x WHERE labels IS NOT NULL").fetchall():
        for l in set((r["labels"] or "").split("|")):
            if l:
                lab[l] = lab.get(l, 0) + 1
    out["labels"] = [{"value": k, "count": v}
                     for k, v in sorted(lab.items(), key=lambda kv: (-kv[1], kv[0]))[:200]]
    out["total"] = conn.execute(f"SELECT COUNT(*) FROM ({BASE}) x").fetchone()[0]
    return out


def _clean(field: str, value) -> str | None:
    v = "" if value is None else str(value).strip()
    if len(v) > MAX_LEN:
        raise ApiError(400, f"{field}: value too long")
    if field == "email" and v:
        em = N.normalize_email(v)
        if not em or not N.is_valid_email(em):
            raise ApiError(400, "email: not a valid address")
        return em
    if field in ("linkedin_url", "photo_url") and v and not re.match(r"^https?://", v, re.I):
        raise ApiError(400, f"{field}: must be an http(s) URL")
    if field == "state" and v:
        st = N.normalize_state(v)
        if not st:
            raise ApiError(400, "state: not a recognised US state")
        return st
    return v or None


def _edit(conn, user: str, cid: int, body: dict) -> dict:
    from ..db.repository import Repository
    from ..model import Address, CanonicalRecord, Email, Phone, Tag
    from ..resolve import Resolver

    if not conn.execute("SELECT 1 FROM contacts WHERE contact_id=? AND is_deleted=0", (cid,)).fetchone():
        raise ApiError(404, "no such contact")
    bad = [k for k in body if k not in EDITABLE]
    if bad:
        raise ApiError(400, f"not editable: {', '.join(sorted(bad))}")
    repo = Repository(conn)
    origin = f"ui:{user}"
    changed = []
    names = {}
    for field, raw in body.items():
        val = _clean(field, raw)
        if field in ("first_name", "last_name", "title", "linkedin_url", "photo_url"):
            conn.execute(f"UPDATE contacts SET {field}=?, updated_at=datetime('now') WHERE contact_id=?",
                         (val, cid))
            if field in ("first_name", "last_name"):
                names[field] = val
        elif field == "email":
            if val:
                conn.execute("UPDATE emails SET is_primary=0 WHERE contact_id=?", (cid,))
                repo.add_email(Email(email=val, email_norm=val, is_primary=True), cid, None)
                conn.execute("UPDATE emails SET is_primary=1 WHERE contact_id=? AND email_norm=?", (cid, val))
        elif field == "phone":
            if val:
                repo.add_phone(Phone(phone_raw=val, phone_e164=N.normalize_phone(val)), cid, None)
        elif field in ("role", "trade", "project"):
            conn.execute("DELETE FROM entity_tags WHERE entity_type='contact' AND entity_id=? AND tag_id IN "
                         "(SELECT tag_id FROM tags WHERE kind=?)", (cid, field))
            if val:
                repo.add_tag(Tag(field, val), "contact", cid)
        elif field == "company":
            if val:
                rec = CanonicalRecord(source="ui", org_name=val, org_name_norm=N.org_name_norm(val))
                oid = Resolver(repo).resolve_org(rec, origin)
                conn.execute("UPDATE contacts SET org_id=?, updated_at=datetime('now') WHERE contact_id=?", (oid, cid))
            else:
                conn.execute("UPDATE contacts SET org_id=NULL, updated_at=datetime('now') WHERE contact_id=?", (cid,))
        elif field in ("city", "state"):
            row = conn.execute("SELECT address_id, line1, city, state, zip FROM addresses "
                               "WHERE contact_id=? ORDER BY address_id LIMIT 1", (cid,)).fetchone()
            cur = dict(row) if row else {"line1": None, "city": None, "state": None, "zip": None}
            cur[field] = val
            norm = N.addr_norm(cur["line1"], cur["city"], cur["state"], cur["zip"]) or "-"
            if row:
                conn.execute("UPDATE addresses SET city=?, state=?, addr_norm=? WHERE address_id=?",
                             (cur["city"], cur["state"], norm, row["address_id"]))
            else:
                repo.add_address(Address(city=cur["city"], state=cur["state"], addr_norm=norm), cid, None)
            conn.execute("UPDATE contacts SET updated_at=datetime('now') WHERE contact_id=?", (cid,))
        changed.append(field)
        repo.log_change("contact", cid, "update", origin, field)
    if names:
        c = conn.execute("SELECT first_name, last_name FROM contacts WHERE contact_id=?", (cid,)).fetchone()
        full = " ".join(x for x in (c["first_name"], c["last_name"]) if x) or None
        conn.execute("UPDATE contacts SET full_name=?, name_norm=?, block_key=?, updated_at=datetime('now') "
                     "WHERE contact_id=?",
                     (full, N.name_norm(c["first_name"], c["last_name"], full),
                      N.block_key(c["first_name"], c["last_name"], N.name_norm(c["first_name"], c["last_name"], full)),
                      cid))
    repo._reindex_contact(cid)
    conn.commit()
    row = conn.execute(f"SELECT * FROM ({BASE}) x WHERE id=?", (cid,)).fetchone()
    return {"ok": True, "changed": changed, "contact": _shape(dict(row)) if row else None}


def _labels(conn, user: str, cid: int, body: dict) -> dict:
    from ..db.repository import Repository
    from ..model import Tag
    if not conn.execute("SELECT 1 FROM contacts WHERE contact_id=? AND is_deleted=0", (cid,)).fetchone():
        raise ApiError(404, "no such contact")
    repo = Repository(conn)
    for v in body.get("add") or []:
        v = str(v).strip()[:80]
        if v:
            repo.add_tag(Tag("label", v), "contact", cid)
    for v in body.get("remove") or []:
        conn.execute("DELETE FROM entity_tags WHERE entity_type='contact' AND entity_id=? AND tag_id IN "
                     "(SELECT tag_id FROM tags WHERE kind='label' AND value=?)", (cid, str(v).strip()))
    repo.log_change("contact", cid, "update", f"ui:{user}", "labels")
    conn.execute("UPDATE contacts SET updated_at=datetime('now') WHERE contact_id=?", (cid,))
    conn.commit()
    return {"ok": True}


# -- reports (doc-engine specs) ------------------------------------------------

REPORTS = {
    "directory": "Project Directory",
    "full": "Full Contact Directory",
    "trade": "Subcontractors by Trade",
    "company": "Company / Entity Rollup",
    "label": "Group / Label Rollup",
}
_MAX_ROWS = 600
# Portrait (the org default, 8.5x11) drops Title so the Email column is wide enough
# that no link wraps mid-string — the doc engine's audit fails the render otherwise.
_COLS = {"portrait": (["Role", "Name", "Company", "Phone #", "Email"], [13, 17, 22, 15, 33]),
         "landscape": (["Role", "Name", "Title", "Company", "Phone #", "Email"], [10, 15, 16, 19, 13, 27])}


def _fmt_phone(p: str | None) -> str:
    d = re.sub(r"\D", "", p or "")
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return f"{d[:3]}-{d[3:6]}-{d[6:]}" if len(d) == 10 else (p or "")


def _t(v) -> str:
    """Contact data is untrusted (it comes from Gmail/Calendar/CRMs) and the doc
    engine renders specs in headless Chromium, so strip angle brackets from every
    dynamic string — a name like '<img src=http://internal/>' must stay inert."""
    return re.sub(r"[<>]", "", "" if v is None else str(v)).strip()


def _row(r: dict, orient: str) -> list:
    base = [r.get("role") or r.get("trade") or "", r.get("full_name") or ""]
    if orient == "landscape":
        base.append(r.get("title") or "")
    return [_t(x) for x in base + [r.get("company") or "", _fmt_phone(r.get("phone")), r.get("email") or ""]]


def _summary_section(total: int, rows: list) -> dict:
    cos = {r.get("company") for r in rows if r.get("company")}
    sts = {r.get("state") for r in rows if r.get("state")}
    with_email = sum(1 for r in rows if r.get("email"))
    pct = round(100 * with_email / len(rows)) if rows else 0
    return {"title": "Summary", "flow": [{"type": "stats", "items": [
        {"value": f"{total:,}", "label": "Contacts", "sub": "match the current filters"},
        {"value": f"{len(cos):,}", "label": "Companies / entities"},
        {"value": f"{len(sts):,}", "label": "States"},
        {"value": f"{pct}%", "label": "With email on file"}]}]}


def _directory_bucket(r: dict) -> str:
    role = (r.get("role") or "").lower()
    if "ntxp" in (r.get("company") or "").lower():
        return "NTXP LLC"
    if role in ("owner", "inspector"):
        return "Owner / Inspectors"
    if role in ("engineer", "consultant", "architect"):
        return "Design Team"
    return "Subcontractors"


def _report_spec(conn, query: dict) -> dict:
    kind = _q1(query, "type", "full")
    orient = _q1(query, "orientation", "portrait")     # org default: 8.5x11 portrait
    if orient not in ("portrait", "landscape"):
        raise ApiError(400, "orientation must be portrait or landscape")
    if kind not in REPORTS:
        raise ApiError(400, f"unknown report; one of {', '.join(REPORTS)}")
    total, rows = _rows(conn, query, _MAX_ROWS)
    proj = _t(", ".join(_qall(query, "project")) or ", ".join(_qall(query, "company")) or "All Contacts")
    note = f" (first {_MAX_ROWS} of {total})" if total > _MAX_ROWS else ""
    cols, widths = _COLS[orient]

    def section(title, rs):
        return {"title": _t(title), "columns": cols, "widths": widths,
                "rows": [_row(r, orient) for r in rs] or [["", "to confirm"] + [""] * (len(cols) - 2)]}

    groups: dict[str, list] = {}
    for r in rows:
        if kind == "directory":
            groups.setdefault(_directory_bucket(r), []).append(r)
        elif kind == "trade":
            groups.setdefault(r.get("trade") or "Unassigned", []).append(r)
        elif kind == "company":
            groups.setdefault(r.get("company") or "Unaffiliated", []).append(r)
        elif kind == "label":
            for l in (r.get("labels") or ["Unlabelled"]):
                groups.setdefault(l, []).append(r)
        else:
            groups.setdefault("Contacts", []).append(r)
    if kind == "directory":
        order = ["Owner / Inspectors", "Design Team", "NTXP LLC", "Subcontractors"]
        body = [section(k, groups.get(k, [])) for k in order]
    else:
        body = [section(k, v) for k, v in sorted(groups.items(), key=lambda kv: kv[0].lower())] \
            or [section("Contacts", [])]
    return {
        "doc_title": REPORTS[kind], "project_title": proj + note, "orientation": orient,
        "meta": [["CONTACTS", f"{total:,}"], ["SOURCE", "NTXP canonical contacts"]],
        "footer_left": "NTXP LLC  ·  Woman-Owned  ·  HUB Certified",
        "footer_center": f"{REPORTS[kind]} — {proj}",
        "show_counts": True, "max_wrap_lines": 2,
        "key_strip": "<b>KEY</b>&nbsp;&nbsp; Every email and phone number on this page is a live link. "
                     "&nbsp;·&nbsp; Source of truth: Lightfield, reconciled nightly.",
        "sections": [_summary_section(total, rows)] + body, "variant": "ntxp",
    }


_CUSTOM_FIELDS = {"name": "full_name", "role": "role", "trade": "trade", "company": "company",
                  "title": "title", "city": "city", "state": "state", "project": "project",
                  "email": "email", "phone #": "phone", "phone": "phone"}


def _custom_spec(conn, query: dict, tpl: dict) -> dict:
    """Fill an uploaded template's layout (columns/widths/title only) with live
    filtered data. The template contributes labels, never content."""
    cols = [_t(c)[:40] for c in (tpl.get("columns") or [])][:12]
    if not cols:
        raise ApiError(400, "template has no columns")
    keys = [_CUSTOM_FIELDS.get(c.lower()) for c in cols]
    widths = tpl.get("widths") or []
    if not (len(widths) == len(cols) and all(isinstance(w, (int, float)) and 3 <= w <= 80 for w in widths)):
        widths = None
    orient = _q1(query, "orientation", "portrait")
    if orient not in ("portrait", "landscape"):
        raise ApiError(400, "orientation must be portrait or landscape")
    title = _t(tpl.get("doc_title") or "Custom Report")[:60] or "Custom Report"
    total, rows = _rows(conn, query, _MAX_ROWS)
    proj = _t(", ".join(_qall(query, "project")) or "All Contacts")

    def val(r, k):
        v = _fmt_phone(r.get("phone")) if k == "phone" else (r.get(k) if k else "")
        return _t(v)
    sec = {"title": "Contacts", "columns": cols, "rows": [[val(r, k) for k in keys] for r in rows]
           or [["to confirm"] + [""] * (len(cols) - 1)]}
    if widths:
        sec["widths"] = widths
    return {"doc_title": title, "project_title": proj, "orientation": orient,
            "meta": [["CONTACTS", f"{total:,}"], ["SOURCE", "NTXP canonical contacts"]],
            "footer_left": "NTXP LLC  ·  Woman-Owned  ·  HUB Certified", "footer_center": title,
            "show_counts": True, "max_wrap_lines": 2, "variant": "ntxp",
            "sections": [_summary_section(total, rows), sec]}


def _render(spec: dict, fmt: str):
    """Render a doc-engine spec to PDF/DOCX with the NTXP Branded Document engine
    (set NTXP_DOC_ENGINE to its scripts/render.py). 501 if not installed."""
    import os
    import subprocess
    import sys
    import tempfile
    if fmt not in ("pdf", "docx"):
        raise ApiError(400, "format must be pdf or docx")
    engine = os.environ.get("NTXP_DOC_ENGINE")
    if not engine or not os.path.exists(engine):
        return _json(501, {"error": "doc engine not configured on this server "
                                    "(set NTXP_DOC_ENGINE to the skill's scripts/render.py)"})
    with tempfile.TemporaryDirectory() as td:
        sp, out = os.path.join(td, "spec.json"), os.path.join(td, "report.pdf")
        with open(sp, "w") as fh:
            json.dump(spec, fh)
        py = os.environ.get("NTXP_DOC_PYTHON", sys.executable)
        try:
            pr = subprocess.run([py, engine, sp, out], capture_output=True, text=True, timeout=150)
        except subprocess.TimeoutExpired:
            return _json(504, {"error": "report render timed out"})
        path = out if fmt == "pdf" else out[:-4] + ".docx"
        if pr.returncode != 0 or not os.path.exists(path):
            return _json(422, {"error": "doc engine audit failed", "detail": (pr.stdout + pr.stderr)[-1500:]})
        with open(path, "rb") as fh:
            data = fh.read()
    ctype = "application/pdf" if fmt == "pdf" else \
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return 200, ctype, data


def _csv(conn, query: dict) -> str:
    _, rows = _rows(conn, query, None)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ID", "First", "Last", "Company", "Title", "Role", "Trade", "City", "State",
                "Phone", "Email", "Labels", "Project", "LinkedIn", "Grade"])
    for r in rows:
        w.writerow([r["id"], r["first_name"], r["last_name"], r["company"], r["title"], r["role"],
                    r["trade"], r["city"], r["state"], r["phone"], r["email"],
                    "; ".join(r["labels"]), r["project"], r["linkedin_url"], r["grade"]])
    return buf.getvalue()


# -- dispatcher ----------------------------------------------------------------

def handle(conn, user: str, method: str, path: str, query: dict, body: dict):
    """-> (status, content_type, payload bytes). Raises nothing: ApiError -> JSON."""
    try:
        p = path.rstrip("/")
        m = method.upper()
        if p == "/api/me" and m == "GET":
            return _json(200, {"email": user})
        if p == "/api/contacts" and m == "GET":
            limit = min(int(_q1(query, "limit", "100") or 100), 5000)
            offset = max(int(_q1(query, "offset", "0") or 0), 0)
            total, rows = _rows(conn, query, limit, offset)
            return _json(200, {"total": total, "offset": offset, "limit": limit, "rows": rows})
        if p == "/api/facets" and m == "GET":
            return _json(200, _facets(conn, query))
        mm = re.match(r"^/api/contacts/(\d+)$", p)
        if mm and m == "PATCH":
            return _json(200, _edit(conn, user, int(mm.group(1)), body or {}))
        mm = re.match(r"^/api/contacts/(\d+)/labels$", p)
        if mm and m == "POST":
            return _json(200, _labels(conn, user, int(mm.group(1)), body or {}))
        if p == "/api/report" and m == "GET":
            spec = _report_spec(conn, query)
            total = conn.execute(f"SELECT COUNT(*) FROM ({BASE}) x" + _filters(query)[0],
                                 _filters(query)[1]).fetchone()[0] if not _q1(query, "near") else None
            return _json(200, {"spec": spec, "total": total, "capped_at": _MAX_ROWS})
        if p == "/api/report/render" and m == "GET":
            return _render(_report_spec(conn, query), _q1(query, "format", "pdf"))
        if p == "/api/report/custom" and m == "POST":
            return _json(200, {"spec": _custom_spec(conn, query, body or {})})
        if p == "/api/report/render-custom" and m == "POST":
            return _render(_custom_spec(conn, query, body or {}), _q1(query, "format", "pdf"))
        if p == "/api/export.csv" and m == "GET":
            return 200, "text/csv; charset=utf-8", _csv(conn, query).encode()
        if p == "/api/council" and m == "GET":
            from ..council import effectiveness, list_answers
            return _json(200, {"effectiveness": effectiveness(conn), "recent": list_answers(conn, 50)})
        return _json(404, {"error": "not found"})
    except ApiError as e:
        return _json(e.status, {"error": e.msg})
    except (ValueError, TypeError) as e:
        return _json(400, {"error": str(e)})


def _json(status: int, obj) -> tuple[int, str, bytes]:
    return status, "application/json", json.dumps(obj, default=str).encode()


def parse_query(qs: str) -> dict:
    """Repeated keys stay lists (checklist filters); single keys collapse to str."""
    return {k: (v if len(v) > 1 else v[0]) for k, v in parse_qs(qs, keep_blank_values=False).items()}
