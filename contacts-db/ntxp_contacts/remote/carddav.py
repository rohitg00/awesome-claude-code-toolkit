"""Minimal read-only CardDAV collection for one-way iOS/macOS contact sync.

Implements the discovery + query flow Apple Contacts needs — OPTIONS, PROPFIND
(current-user-principal → addressbook-home-set → the addressbook collection and
its items), REPORT (addressbook-query / addressbook-multiget), and GET of a
`.vcf` — all **read-only**. Token-gated by the same OAuth verifier as the MCP, so
a new hire gets day-one, one-way access with nothing writing back.

End-to-end device validation needs a real iOS client; handlers here are unit-
tested for well-formed multistatus XML and vCard payloads.
"""
from __future__ import annotations

import xml.sax.saxutils as sx

import hashlib

from .auth import verify_token
from .vcard import exposed_rows, is_exposed, render_one, uid

BASE = "/carddav"
PRINCIPAL = f"{BASE}/principal/"
HOME = f"{BASE}/addressbooks/"
COLLECTION = f"{BASE}/addressbooks/ntxp/"
_D = 'xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav"'


def _ms(inner: str) -> bytes:
    return (f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<d:multistatus {_D}>{inner}</d:multistatus>').encode()


def _ok(href: str, prop: str) -> str:
    return (f"<d:response><d:href>{sx.escape(href)}</d:href><d:propstat>"
            f"<d:prop>{prop}</d:prop><d:status>HTTP/1.1 200 OK</d:status>"
            f"</d:propstat></d:response>")


def _exposed_map(conn) -> dict[int, str]:
    """{contact_id: revision} for exposed contacts (the only ones served)."""
    return dict(exposed_rows(conn))


def _ctag_from(emap: dict[int, str]) -> str:
    """Collection tag that advances on any add/remove/edit/exposure change —
    derived from the exposed set's size and newest revision, not just max id."""
    newest = max(emap.values(), default="0")
    return hashlib.md5(f"{len(emap)}:{newest}".encode()).hexdigest()[:16]


def _item_href(cid: int) -> str:
    return f"{COLLECTION}{uid(cid)}.vcf"


def _etag(cid: int, rev: str) -> str:
    return '"' + hashlib.md5(f"{cid}:{rev}".encode()).hexdigest()[:16] + '"'


def handle(conn, method: str, path: str, body: str, depth: str) -> tuple[int, list, bytes]:
    """Return (status, extra_headers, body) for a CardDAV request."""
    method = method.upper()
    if method == "OPTIONS":
        return 200, [(b"dav", b"1, 2, 3, addressbook"),
                     (b"allow", b"OPTIONS, GET, PROPFIND, REPORT")], b""

    if method == "GET":
        cid = _cid_from_path(path)
        # Gate direct item reads on the exposure/tombstone state, not just the
        # collection listing — a guessed ntxp-<id>.vcf must not leak a held-back
        # or deleted contact.
        if cid is not None and is_exposed(conn, cid):
            vc = render_one(conn, cid)
            if vc:
                return 200, [(b"content-type", b"text/vcard; charset=utf-8")], vc.encode()
        return 404, [], b"not found"

    if method == "PROPFIND":
        p = path.rstrip("/") + "/"
        if p in (BASE + "/", "/", "/.well-known/carddav/"):
            return 207, [], _ms(_ok(BASE + "/",
                f"<d:current-user-principal><d:href>{PRINCIPAL}</d:href></d:current-user-principal>"))
        if p == PRINCIPAL:
            return 207, [], _ms(_ok(PRINCIPAL,
                f"<card:addressbook-home-set><d:href>{HOME}</d:href></card:addressbook-home-set>"
                f"<d:current-user-principal><d:href>{PRINCIPAL}</d:href></d:current-user-principal>"))
        if p in (HOME, COLLECTION):
            emap = _exposed_map(conn)
            ctag = _ctag_from(emap)
            coll_prop = ("<d:resourcetype><d:collection/><card:addressbook/></d:resourcetype>"
                         "<d:displayname>NTXP Contacts</d:displayname>"
                         f"<cs:getctag xmlns:cs=\"http://calendarserver.org/ns/\">{ctag}</cs:getctag>")
            responses = _ok(COLLECTION, coll_prop)
            if depth and depth != "0":
                for cid, rev in emap.items():
                    responses += _ok(_item_href(cid),
                                     f"<d:getetag>{_etag(cid, rev)}</d:getetag>"
                                     "<d:getcontenttype>text/vcard</d:getcontenttype>")
            return 207, [], _ms(responses)
        cid = _cid_from_path(path)
        if cid is not None:
            emap = _exposed_map(conn)
            if cid not in emap:
                return 404, [], b"not found"
            return 207, [], _ms(_ok(_item_href(cid),
                f"<d:getetag>{_etag(cid, emap[cid])}</d:getetag>"))
        return 404, [], b"not found"

    if method == "REPORT":
        emap = _exposed_map(conn)
        want = _hrefs_in(body)
        # Multiget hrefs are client-supplied — intersect with the exposed set so
        # an explicit href cannot pull a held-back/deleted contact.
        cids = [c for c in (_cid_from_path(h) for h in want) if c in emap] \
            if want else list(emap)
        responses = ""
        for cid in cids:
            vc = render_one(conn, cid)
            if not vc:
                continue
            responses += _ok(_item_href(cid),
                             f"<d:getetag>{_etag(cid, emap[cid])}</d:getetag>"
                             f"<card:address-data>{sx.escape(vc)}</card:address-data>")
        return 207, [], _ms(responses)

    return 405, [], b"method not allowed"


def _cid_from_path(path: str) -> int | None:
    name = path.rsplit("/", 1)[-1]
    if name.startswith(uid(0)[:5]) and name.endswith(".vcf"):  # "ntxp-<id>.vcf"
        try:
            return int(name[len("ntxp-"):-len(".vcf")])
        except ValueError:
            return None
    return None


def _hrefs_in(body: str) -> list[str]:
    import re
    return re.findall(r"<[a-zA-Z0-9]*:?href>\s*([^<]+?)\s*</[a-zA-Z0-9]*:?href>", body or "")


class CardDAVApp:
    """ASGI app for the read-only CardDAV collection (token-gated)."""

    def __init__(self, db_override=None):
        self.db_override = db_override

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers") or []}
        auth = headers.get("authorization", "")
        token = auth[7:].strip() if auth[:7].lower() == "bearer " else ""
        if verify_token(token) is None:
            return await _respond(send, 401, [(b"www-authenticate", b"Bearer")],
                                  b'{"error":"unauthorized"}')
        body = b""
        more = True
        while more:
            msg = await receive()
            body += msg.get("body", b"")
            more = msg.get("more_body", False)
        from ..db import connect, migrate
        conn = connect(self.db_override)
        migrate(conn)
        status, extra, payload = handle(conn, scope["method"], scope["path"],
                                        body.decode("utf-8", "replace"),
                                        headers.get("depth", "0"))
        await _respond(send, status, extra, payload)


async def _respond(send, status, headers, body: bytes):
    hdrs = list(headers) + [(b"content-length", str(len(body)).encode())]
    await send({"type": "http.response.start", "status": status, "headers": hdrs})
    await send({"type": "http.response.body", "body": body})
