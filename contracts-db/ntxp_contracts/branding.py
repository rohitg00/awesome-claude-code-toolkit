"""Branding resolver — finds the *most up-to-date* brand skill in Claude's
settings on every call and turns it into a palette + fonts the dashboard styles
itself from.

Why resolve at request time instead of baking colors in: the user asked that
the database "search for the most up to date Branding skill each time in
Claude's settings" so that whenever the NTXP brand skill is updated, every
screen this package renders picks the change up automatically — no redeploy.

Search order (first match per location, newest mtime wins across them):
  1. $CLAUDE_CONFIG_DIR/skills           (explicit override)
  2. ~/.claude/skills                    (user skills)
  3. ~/.config/claude/skills
  4. <repo>/skills                       (project skills, incl. this toolkit)
  5. ~/.claude/plugins/**/skills
  6. /mnt/skills (+ /mnt/skills/examples)  (managed skills)

A skill qualifies as a brand skill if its name/description/keywords mention
NTXP brand identity or generic branding. NTXP-specific skills outrank generic
ones; among equals, the most recently modified SKILL.md wins. If nothing is
found we fall back to documented NTXP defaults so the UI is never unstyled.
"""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

# --- NTXP fallback brand -----------------------------------------------------
# Web-safe fallback stack appended after whatever heading/body family a skill
# names (or the defaults below) — defined once so it can't drift.
_FALLBACK_STACK = ", 'Segoe UI', Arial, sans-serif"

# Placeholder defaults used only when no brand skill is discovered. They are
# intentionally neutral/professional; the real NTXP palette comes from the
# brand skill the moment one is present in Claude's settings.
NTXP_DEFAULTS = {
    "name": "NTXP",
    "source": "built-in default",
    "colors": {
        "dark": "#10243E",       # primary text / navy
        "light": "#F7F8FA",      # page background
        "surface": "#FFFFFF",    # cards / table
        "muted": "#6B7785",      # secondary text
        "border": "#DCE2EA",     # hairlines
        "primary": "#10243E",    # brand navy
        "accent": "#E2562B",     # safety orange
        "accent2": "#2F80ED",    # link blue
        "success": "#2E7D52",    # executed / good
        "warning": "#B7791F",    # expiring soon
        "danger": "#C0392B",     # unexecuted / expired
    },
    "fonts": {
        "heading": "Poppins" + _FALLBACK_STACK,
        "body": "Inter" + _FALLBACK_STACK,
    },
    "logo": None,
}

_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
# Map free-text color labels found in a SKILL.md to our semantic slots.
_LABEL_MAP = {
    "primary": "primary", "brand": "primary", "navy": "primary",
    "accent": "accent", "orange": "accent", "secondary": "accent2",
    "blue": "accent2", "dark": "dark", "text": "dark",
    "light": "light", "background": "light", "surface": "surface",
    "muted": "muted", "gray": "muted", "grey": "muted", "border": "border",
    "success": "success", "green": "success", "warning": "warning",
    "danger": "danger", "error": "danger", "red": "danger",
}


@dataclass
class Brand:
    name: str
    source: str
    colors: dict
    fonts: dict
    logo: str | None = None
    skill_path: str | None = None
    keywords: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _candidate_skill_dirs() -> list[Path]:
    dirs: list[Path] = []
    cfg = os.environ.get("CLAUDE_CONFIG_DIR")
    if cfg:
        dirs.append(Path(cfg) / "skills")
    home = Path.home()
    dirs += [
        home / ".claude" / "skills",
        home / ".config" / "claude" / "skills",
        Path(__file__).resolve().parents[2] / "skills",   # <repo>/skills
        home / ".claude" / "plugins",
        Path("/mnt/skills"),   # recursive — covers /mnt/skills/examples too
    ]
    extra = os.environ.get("NTXP_BRANDING_PATH")
    if extra:
        dirs.append(Path(extra).expanduser())
    return [d for d in dirs if d.exists()]


def _iter_skill_files() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for d in _candidate_skill_dirs():
        for sk in d.rglob("SKILL.md"):
            rp = sk.resolve()
            if rp not in seen:
                seen.add(rp)
                out.append(sk)
    return out


def _score_brand_skill(text: str) -> int:
    """Higher = more likely the intended brand skill. 0 = not a brand skill."""
    head = text[:1500].lower()
    score = 0
    if re.search(r"\bbrand", head) or "brand-guidelines" in head:
        score += 2
    if any(k in head for k in ("brand color", "visual identity", "corporate identity",
                               "style guide", "typography", "logo")):
        score += 1
    if "ntxp" in head:
        score += 10          # NTXP-specific brand skill always wins
    return score


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    fm: dict = {}
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip().lower()] = v.strip()
    return fm


def _parse_colors(text: str) -> dict:
    """Pull labelled hex colors out of a SKILL.md body.

    Matches lines like ``- Orange: `#d97757` - Primary accent`` or
    ``Primary: #10243E`` and maps the label onto our semantic slots.
    """
    colors: dict = {}
    for line in text.splitlines():
        hexes = _HEX_RE.findall(line)
        if not hexes:
            continue
        label_part = line.split(hexes[0])[0].lower()
        slot = None
        for key, mapped in _LABEL_MAP.items():
            if key in label_part:
                slot = mapped
                break
        if slot and slot not in colors:
            colors[slot] = hexes[0]
    return colors


_FONT_PATTERNS = (
    ("heading", r"head(?:ing|line)s?\**\s*[:\-]?\s*([A-Za-z][\w '\-,]+)"),
    ("body", r"body(?:\s*text)?\**\s*[:\-]?\s*([A-Za-z][\w '\-,]+)"),
)


def _parse_fonts(text: str) -> dict:
    fonts: dict = {}
    for slot, pattern in _FONT_PATTERNS:
        m = re.search(pattern, text, re.I)
        if m:
            fonts[slot] = m.group(1).split("(")[0].strip().rstrip(".") + _FALLBACK_STACK
    return fonts


def resolve_brand() -> Brand:
    """Scan Claude's settings for the freshest brand skill and build a Brand.
    Always returns something usable (NTXP defaults if no skill is found)."""
    best: tuple[int, float, Path, str] | None = None
    for sk in _iter_skill_files():
        try:
            text = sk.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        score = _score_brand_skill(text)
        if score <= 0:
            continue
        mtime = sk.stat().st_mtime
        if best is None or (score, mtime) > (best[0], best[1]):
            best = (score, mtime, sk, text)   # keep the text — no second read

    if best is None:
        return Brand(**NTXP_DEFAULTS)

    sk, text = best[2], best[3]
    fm = _parse_frontmatter(text)

    parsed = _parse_colors(text)
    colors = dict(NTXP_DEFAULTS["colors"])
    colors.update(parsed)
    # Let the skill drive the primary brand color: prefer an explicit primary,
    # else the skill's dark, else its accent — only then the built-in default.
    if "primary" not in parsed:
        colors["primary"] = parsed.get("dark") or parsed.get("accent") \
            or NTXP_DEFAULTS["colors"]["primary"]

    fonts = dict(NTXP_DEFAULTS["fonts"])
    fonts.update(_parse_fonts(text))

    logo = None
    for cand in ("logo.svg", "logo.png", "assets/logo.svg", "assets/logo.png"):
        if (sk.parent / cand).exists():
            logo = str(sk.parent / cand)
            break

    name = fm.get("name") or NTXP_DEFAULTS["name"]
    return Brand(
        name=name,
        source=f"skill: {sk}",
        colors=colors,
        fonts=fonts,
        logo=logo,
        skill_path=str(sk),
        keywords=[w.strip() for w in fm.get("description", "").split(",") if w.strip()][:6],
    )
