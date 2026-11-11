"""Live location links for addresses (injected next to any contact address)."""
from __future__ import annotations

from urllib.parse import quote_plus


def _fmt(parts: dict | str) -> str:
    if isinstance(parts, str):
        return parts.strip()
    return ", ".join(str(parts[k]).strip() for k in ("line1", "city", "state", "zip")
                     if parts.get(k))


def maps_link(address: dict | str) -> str | None:
    """Google Maps search URL for an address dict or string."""
    q = _fmt(address)
    if not q:
        return None
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(q)


def apple_maps_link(address: dict | str) -> str | None:
    """Apple Maps URL (for iOS clients)."""
    q = _fmt(address)
    if not q:
        return None
    return "https://maps.apple.com/?q=" + quote_plus(q)
