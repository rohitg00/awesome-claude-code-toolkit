"""Server-side report rendering through the real NTXP document engine.

Skipped unless NTXP_DOC_ENGINE points at the engine's scripts/render.py (it is proprietary and not in this repo).
The point: every report type must come back audit-clean (engine exit 0) in portrait, the org default.
"""
import json
import os

import pytest

from ntxp_contacts.db import connect, migrate
from ntxp_contacts.loaders.base import import_records
from ntxp_contacts.remote.api import handle
from test_api import DATA, _Loader

ENGINE = os.environ.get("NTXP_DOC_ENGINE")
pytestmark = pytest.mark.skipif(not (ENGINE and os.path.exists(ENGINE)), reason="NTXP_DOC_ENGINE not set")


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "r.db")
    migrate(c)
    import_records(c, _Loader(DATA), "x")
    return c


@pytest.mark.parametrize("kind", ["directory", "full", "trade", "company", "label"])
def test_report_renders_audit_clean(conn, kind):
    status, ctype, body = handle(conn, "t@ntxpllc.com", "GET", "/api/report/render",
                                 {"type": kind, "orientation": "portrait", "format": "pdf"}, {})
    assert status == 200, body[:300]
    assert ctype == "application/pdf" and body.startswith(b"%PDF")


def test_untrusted_markup_stays_inert(conn):
    # a contact name that tries to smuggle HTML into the renderer
    conn.execute("UPDATE contacts SET full_name='<img src=http://169.254.169.254/x>Eve' WHERE last_name='Vaden'")
    conn.commit()
    s, _, spec = handle(conn, "t@ntxpllc.com", "GET", "/api/report", {"type": "full"}, {})
    assert "<img" not in spec.decode() and "<" not in json.dumps(json.loads(spec)["spec"]["sections"])
