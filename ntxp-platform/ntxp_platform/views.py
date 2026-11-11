"""Views: which apps' functions each subdomain may reach (inputs/outputs differ per view).

* contacts / contracts — their own app plus read-only cross-links to each other.
* apilog — only itself: it holds credentials, so nothing else can be called from it and it
  can't be called from elsewhere (``get_credentials`` is additionally ``sensitive``).
* all — the combined, non-sensitive surface (what the central MCP gateway exposes).
"""
VIEWS: dict[str, set[str]] = {
    "contacts": {"contacts", "contracts", "links"},
    "contracts": {"contracts", "contacts", "links"},
    "apilog": {"apilog"},
    "all": {"contacts", "contracts", "apilog", "links"},
}


def allowed(view: str, app: str) -> bool:
    return app in VIEWS.get(view, set())
