"""UserPromptSubmit hook: detect contact mentions in the prompt and inject a
context block — contact cards, blue hotlinks, live Maps location links, and a
preview of potential alternate contact info.

Wire it (plugin ships this automatically; or add to settings.json):

    {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command",
      "command": "python -m ntxp_contacts.hooks.contact_context"}]}]}}

Fail-safe: any error exits 0 with no output, never blocking the prompt. Reads
the DB from NTXP_DB_URL / NTXP_DB_PATH like the rest of the toolkit.
"""
from __future__ import annotations

import json
import sys


def card_text(card: dict) -> str:
    """One contact as injected context: identity, reach, location link, grade, alternates, plus
    the contracts their organization holds with NTXP (Master Contracts) and any current
    scheduled work (Schedules)."""
    bits = [f"**{card.get('name') or 'contact'}**"]
    meta = " · ".join(x for x in (card.get("title"), card.get("org")) if x)
    if meta:
        bits.append(meta)
    if card.get("email"):
        bits.append(f"✉ {card['email']}")
    if card.get("phone"):
        bits.append(f"☎ {card['phone']}")
    if card.get("maps"):
        bits.append(f"📍 {card['address']} <{card['maps']}>")
    if card.get("linkedin_url"):
        bits.append(f"in:{card['linkedin_url']}")
    if card.get("grade") is not None:
        bits.append(f"grade {card.get('grade_band')}·{card.get('grade')}")
    line = " — ".join(bits) + f"  ({card['href']})"
    alts = card.get("alternates") or []
    if alts:
        line += "\n    ↳ possible: " + "; ".join(
            f"{a['field']}={a['value']} ({a['source']} {a['grade']})" for a in alts)
    for c in (card.get("contracts") or [])[:3]:
        flags = f" [{', '.join(c['flags'])}]" if c.get("flags") else ""
        bits = [x for x in (c.get("number"), c.get("title")) if x]
        extra = ", ".join(x for x in (f"coef {c['coefficient']}" if c.get("coefficient") else "",
                                      f"fee {c['cooperative_fee']}" if c.get("cooperative_fee") else "",
                                      f"expires {c['expires']}" if c.get("expires") else "") if x)
        line += f"\n    📄 contract: {' — '.join(bits)}{(' (' + extra + ')') if extra else ''}{flags}"
    for a in (card.get("assignments") or [])[:3]:
        when = " → ".join(x for x in (a.get("start"), a.get("end")) if x)
        line += f"\n    🗓 {a.get('status', 'scheduled')}: {a.get('project') or 'project'}" + (f" ({when})" if when else "")
    return line


_card_line = lambda idx, card: card_text(card)   # noqa: E731  (kept for older callers)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = (data.get("prompt") or data.get("user_prompt")
              or data.get("userPrompt") or "").strip()
    if not prompt:
        return 0
    try:
        from ..db import connect, migrate
        from ..context import HotlinkIndex
        conn = connect(None)
        migrate(conn)
        idx = HotlinkIndex(conn)
        ann = idx.annotate(prompt)
        seen, lines = set(), []
        for link in ann["links"]:
            if link["kind"] == "contact" and link["id"] not in seen:
                seen.add(link["id"])
                card = idx.card(link["id"])
                if card:
                    lines.append("- " + _card_line(idx, card))
        if not lines:
            return 0
        ctx = ("NTXP canonical contacts referenced in this message "
               "(source of truth: Lightfield):\n" + "\n".join(lines))
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ctx,
        }}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
