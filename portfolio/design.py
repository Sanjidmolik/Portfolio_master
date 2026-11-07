"""Design system: defaults, validation and CSS-variable generation.

The admin edits a *draft* design; publishing copies it to the *published*
design that every public page renders. All values are validated against
whitelists / ranges so nothing user-supplied can break out of the <style> tag.
"""
from __future__ import annotations

import copy
import re

from .models import Setting

DRAFT_KEY = "design_draft"
PUBLISHED_KEY = "design_published"

FONTS = {
    # name -> (google families query, css stack)
    "Space Grotesk": ("Space+Grotesk:wght@400;500;600;700", "'Space Grotesk', system-ui, sans-serif"),
    "Sora": ("Sora:wght@400;500;600;700;800", "'Sora', system-ui, sans-serif"),
    "Syne": ("Syne:wght@500;600;700;800", "'Syne', system-ui, sans-serif"),
    "Outfit": ("Outfit:wght@400;500;600;700;800", "'Outfit', system-ui, sans-serif"),
    "Inter": ("Inter:wght@400;500;600;700;800", "'Inter', system-ui, sans-serif"),
    "Manrope": ("Manrope:wght@400;500;600;700;800", "'Manrope', system-ui, sans-serif"),
    "IBM Plex Sans": ("IBM+Plex+Sans:wght@400;500;600;700", "'IBM Plex Sans', system-ui, sans-serif"),
    "DM Sans": ("DM+Sans:wght@400;500;600;700", "'DM Sans', system-ui, sans-serif"),
    "JetBrains Mono": ("JetBrains+Mono:wght@400;500;600;700", "'JetBrains Mono', ui-monospace, monospace"),
    "Playfair Display": ("Playfair+Display:wght@500;600;700;800", "'Playfair Display', Georgia, serif"),
    "Orbitron": ("Orbitron:wght@500;600;700;800", "'Orbitron', system-ui, sans-serif"),
    "Nunito": ("Nunito:wght@400;500;600;700;800", "'Nunito', system-ui, sans-serif"),
    "Rajdhani": ("Rajdhani:wght@500;600;700", "'Rajdhani', system-ui, sans-serif"),
    "Fira Code": ("Fira+Code:wght@400;500;600;700", "'Fira Code', ui-monospace, monospace"),
    "System UI": ("", "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"),
}
MONO_FONT = ("JetBrains+Mono:wght@400;500", "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace")

SECTION_KEYS = ["hero", "about", "experience", "skills", "projects", "education", "github", "contact"]

DEFAULT_SECTIONS = [
    {"key": "hero", "enabled": True, "title": "Signal Acquired", "subtitle": ""},
    {"key": "about", "enabled": True, "title": "About Me",
     "subtitle": "From the master control room to the command line."},
    {"key": "experience", "enabled": True, "title": "Professional Experience",
     "subtitle": "Keeping signals on air, around the clock."},
    {"key": "skills", "enabled": True, "title": "Technology Arsenal",
     "subtitle": "The tools I reach for across code, security and broadcast."},
    {"key": "projects", "enabled": True, "title": "Featured Projects",
     "subtitle": "Things I've designed, built and shipped."},
    {"key": "education", "enabled": True, "title": "Education & Certifications",
     "subtitle": "Where I've studied and what I've earned."},
    {"key": "github", "enabled": True, "title": "GitHub Activity",
     "subtitle": "Live from my public repositories."},
    {"key": "contact", "enabled": True, "title": "Open a Channel",
     "subtitle": "Have an opportunity or a question? My line is open."},
]

DEFAULT_DESIGN = {
    "theme": {"mode": "dark", "allow_toggle": True, "skin": "broadcast"},
    "identity": {"avatar_style": "illustrated"},
    "colors": {
        "primary": "#3b82f6",
        "secondary": "#22d3ee",
        "accent": "#a78bfa",
        "background": "#070b14",
        "surface": "#0d1424",
        "text": "#e6edf7",
        "background_light": "#f5f7fb",
        "surface_light": "#ffffff",
        "text_light": "#0b1220",
    },
    "typography": {
        "heading_font": "Space Grotesk",
        "body_font": "Inter",
        "base_size": 16,
        "heading_weight": 700,
    },
    "layout": {
        "section_spacing": "comfortable",
        "container_width": 1200,
        "radius": 16,
        "card_style": "outline",
        "nav_style": "floating",
    },
    "animation": {
        "enabled": True,
        "speed": 1.0,
        "intensity": "normal",
        "page_transition": "fade",
        "scroll_reveal": "fade-up",
        "background_effects": True,
        "cursor_effects": True,
        "loader": True,
    },
    "sections": DEFAULT_SECTIONS,
}

CHOICES = {
    "theme.mode": ["dark", "light", "system"],
    "identity.avatar_style": ["illustrated", "photo"],
    "theme.skin": ["broadcast", "anime", "programmer", "neon", "ceo", "engineer", "nature"],
    "layout.section_spacing": ["compact", "comfortable", "spacious"],
    "layout.card_style": ["outline", "elevated", "solid", "glass"],
    "layout.nav_style": ["floating", "solid", "minimal"],
    "animation.intensity": ["subtle", "normal", "bold"],
    "animation.page_transition": ["fade", "slide", "none"],
    "animation.scroll_reveal": ["fade-up", "fade", "zoom", "slide", "none"],
}
RANGES = {
    "typography.base_size": (14, 20, int),
    "typography.heading_weight": (400, 800, int),
    "layout.container_width": (960, 1480, int),
    "layout.radius": (0, 32, int),
    "animation.speed": (0.5, 2.0, float),
}
SPACING_PX = {"compact": 72, "comfortable": 112, "spacious": 152}
INTENSITY = {"subtle": 0.5, "normal": 1.0, "bold": 1.6}
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def default_design() -> dict:
    return copy.deepcopy(DEFAULT_DESIGN)


def sanitize(raw: dict | None) -> dict:
    """Merge user input onto defaults, rejecting anything not whitelisted."""
    base = default_design()
    raw = raw if isinstance(raw, dict) else {}

    for group in ("theme", "identity", "colors", "typography", "layout", "animation"):
        incoming = raw.get(group) if isinstance(raw.get(group), dict) else {}
        for key, default in base[group].items():
            if key not in incoming:
                continue
            val = incoming[key]
            path = f"{group}.{key}"
            if path in CHOICES:
                if val in CHOICES[path]:
                    base[group][key] = val
            elif path in RANGES:
                lo, hi, cast = RANGES[path]
                try:
                    num = cast(float(val))
                    base[group][key] = min(hi, max(lo, num))
                except (TypeError, ValueError):
                    pass
            elif group == "colors":
                if isinstance(val, str) and HEX_RE.match(val):
                    base[group][key] = val.lower()
            elif key in ("heading_font", "body_font"):
                if val in FONTS:
                    base[group][key] = val
            elif isinstance(default, bool):
                base[group][key] = val in (True, "true", "on", "1", 1)

    sections_in = raw.get("sections")
    if isinstance(sections_in, list):
        seen, out = set(), []
        defaults = {s["key"]: s for s in DEFAULT_SECTIONS}
        for sec in sections_in:
            if not isinstance(sec, dict) or sec.get("key") not in defaults or sec["key"] in seen:
                continue
            seen.add(sec["key"])
            d = defaults[sec["key"]]
            out.append({
                "key": sec["key"],
                "enabled": True if sec["key"] == "hero" else bool(sec.get("enabled", True)),
                "title": str(sec.get("title") or d["title"])[:80],
                "subtitle": str(sec.get("subtitle") or "")[:240],
            })
        for key in SECTION_KEYS:  # never lose a section
            if key not in seen:
                out.append(copy.deepcopy(defaults[key]))
        # hero is always first
        out.sort(key=lambda s: 0 if s["key"] == "hero" else 1)
        base["sections"] = out
    return base


def get_draft() -> dict:
    stored = Setting.read(DRAFT_KEY)
    return sanitize(stored) if stored else get_published()


def get_published() -> dict:
    return sanitize(Setting.read(PUBLISHED_KEY) or {})


def save_draft(design: dict) -> dict:
    clean = sanitize(design)
    Setting.write(DRAFT_KEY, clean)
    return clean


def publish(design: dict | None = None) -> dict:
    clean = sanitize(design if design is not None else get_draft())
    Setting.write(PUBLISHED_KEY, clean)
    Setting.write(DRAFT_KEY, clean)
    return clean


def has_unpublished_changes() -> bool:
    return get_draft() != get_published()


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2], 16)} {int(h[2:4], 16)} {int(h[4:6], 16)}"


def font_url(design: dict) -> str | None:
    fams = []
    for key in ("heading_font", "body_font"):
        q = FONTS.get(design["typography"][key], ("", ""))[0]
        if q and q not in fams:
            fams.append(q)
    if not any(f.split(":")[0] == MONO_FONT[0].split(":")[0] for f in fams):
        fams.append(MONO_FONT[0])
    if not fams:
        return None
    return "https://fonts.googleapis.com/css2?" + "&".join(f"family={f}" for f in fams) + "&display=swap"


def css_variables(design: dict) -> str:
    """Return a CSS block of custom properties. All inputs are pre-validated."""
    c, t, l, a = design["colors"], design["typography"], design["layout"], design["animation"]
    speed = a["speed"] if a["enabled"] else 1
    dark = [
        f"--bg:{c['background']}", f"--bg-rgb:{_hex_to_rgb(c['background'])}",
        f"--surface:{c['surface']}", f"--surface-rgb:{_hex_to_rgb(c['surface'])}",
        f"--text:{c['text']}", f"--text-rgb:{_hex_to_rgb(c['text'])}",
    ]
    light = [
        f"--bg:{c['background_light']}", f"--bg-rgb:{_hex_to_rgb(c['background_light'])}",
        f"--surface:{c['surface_light']}", f"--surface-rgb:{_hex_to_rgb(c['surface_light'])}",
        f"--text:{c['text_light']}", f"--text-rgb:{_hex_to_rgb(c['text_light'])}",
    ]
    shared = [
        f"--primary:{c['primary']}", f"--primary-rgb:{_hex_to_rgb(c['primary'])}",
        f"--secondary:{c['secondary']}", f"--secondary-rgb:{_hex_to_rgb(c['secondary'])}",
        f"--accent:{c['accent']}", f"--accent-rgb:{_hex_to_rgb(c['accent'])}",
        f"--font-heading:{FONTS[t['heading_font']][1]}",
        f"--font-body:{FONTS[t['body_font']][1]}",
        f"--font-mono:{MONO_FONT[1]}",
        f"--base-size:{t['base_size']}px",
        f"--heading-weight:{t['heading_weight']}",
        f"--section-space:{SPACING_PX[l['section_spacing']]}px",
        f"--container:{l['container_width']}px",
        f"--radius:{l['radius']}px",
        f"--speed:{1 / speed:.3f}",
        f"--intensity:{INTENSITY[a['intensity']]}",
    ]
    return (
        ":root{" + ";".join(shared + dark) + "}"
        ":root[data-theme='light']{" + ";".join(light) + "}"
    )


def body_classes(design: dict) -> str:
    l, a = design["layout"], design["animation"]
    classes = [f"skin-{design['theme']['skin']}", f"card-{l['card_style']}", f"nav-{l['nav_style']}",
               f"avatar-{design['identity']['avatar_style']}",
               f"reveal-{a['scroll_reveal']}", f"transition-{a['page_transition']}"]
    if not a["enabled"]:
        classes.append("no-motion")
    if not a["background_effects"]:
        classes.append("no-bg-fx")
    if not a["cursor_effects"]:
        classes.append("no-cursor-fx")
    return " ".join(classes)


# ---------------------------------------------------------------------------
# One-click theme presets (Design Center > Themes).
# Each preset is a partial design merged onto the defaults; sections are kept
# from the current design when a preset is applied.
# ---------------------------------------------------------------------------
PRESETS = [
    {"key": "broadcast", "name": "TV Broadcast", "tagline": "Master-control-room blues with ON AIR energy.",
     "design": {"theme": {"mode": "dark", "skin": "broadcast"},
                "colors": {"primary": "#3b82f6", "secondary": "#22d3ee", "accent": "#a78bfa",
                           "background": "#070b14", "surface": "#0d1424", "text": "#e6edf7",
                           "background_light": "#f5f7fb", "surface_light": "#ffffff", "text_light": "#0b1220"},
                "typography": {"heading_font": "Space Grotesk", "body_font": "Inter", "base_size": 16, "heading_weight": 700},
                "layout": {"section_spacing": "comfortable", "radius": 16, "card_style": "outline", "nav_style": "floating"},
                "animation": {"enabled": True, "speed": 1.0, "intensity": "normal", "scroll_reveal": "fade-up",
                              "background_effects": True, "cursor_effects": True}}},
    {"key": "anime", "name": "Anime", "tagline": "Sakura pinks, sky blues and playful rounded cards.",
     "design": {"theme": {"mode": "dark", "skin": "anime"},
                "colors": {"primary": "#ff4d9d", "secondary": "#7dd3fc", "accent": "#c084fc",
                           "background": "#130a20", "surface": "#1e1233", "text": "#fdf2ff",
                           "background_light": "#fff5fb", "surface_light": "#ffffff", "text_light": "#2a1035"},
                "typography": {"heading_font": "Nunito", "body_font": "Nunito", "base_size": 16, "heading_weight": 800},
                "layout": {"section_spacing": "comfortable", "radius": 26, "card_style": "glass", "nav_style": "floating"},
                "animation": {"enabled": True, "speed": 1.0, "intensity": "bold", "scroll_reveal": "zoom",
                              "background_effects": True, "cursor_effects": True}}},
    {"key": "programmer", "name": "Programmer", "tagline": "Terminal greens, monospace headings, editor-dark panels.",
     "design": {"theme": {"mode": "dark", "skin": "programmer"},
                "colors": {"primary": "#22c55e", "secondary": "#4ade80", "accent": "#facc15",
                           "background": "#0d1117", "surface": "#161b22", "text": "#e6edf3",
                           "background_light": "#f6f8fa", "surface_light": "#ffffff", "text_light": "#1f2328"},
                "typography": {"heading_font": "JetBrains Mono", "body_font": "Inter", "base_size": 15, "heading_weight": 700},
                "layout": {"section_spacing": "comfortable", "radius": 6, "card_style": "solid", "nav_style": "solid"},
                "animation": {"enabled": True, "speed": 1.0, "intensity": "normal", "scroll_reveal": "fade",
                              "background_effects": True, "cursor_effects": False}}},
    {"key": "neon", "name": "Neon Hacker", "tagline": "Pitch black, toxic green and magenta glow with scanlines.",
     "design": {"theme": {"mode": "dark", "allow_toggle": False, "skin": "neon"},
                "colors": {"primary": "#00e08a", "secondary": "#00e5ff", "accent": "#ff2bd6",
                           "background": "#030405", "surface": "#0a0f0d", "text": "#d4ffe9",
                           "background_light": "#eafff5", "surface_light": "#ffffff", "text_light": "#04130b"},
                "typography": {"heading_font": "Orbitron", "body_font": "JetBrains Mono", "base_size": 15, "heading_weight": 700},
                "layout": {"section_spacing": "comfortable", "radius": 2, "card_style": "outline", "nav_style": "minimal"},
                "animation": {"enabled": True, "speed": 0.9, "intensity": "bold", "scroll_reveal": "slide",
                              "background_effects": True, "cursor_effects": True}}},
    {"key": "ceo", "name": "Professional CEO", "tagline": "Navy and gold, elegant serif headings, calm and minimal.",
     "design": {"theme": {"mode": "light", "skin": "ceo"},
                "colors": {"primary": "#1e3a8a", "secondary": "#a16207", "accent": "#475569",
                           "background": "#0b1020", "surface": "#121a30", "text": "#eef2ff",
                           "background_light": "#f8f7f3", "surface_light": "#ffffff", "text_light": "#0f172a"},
                "typography": {"heading_font": "Playfair Display", "body_font": "Inter", "base_size": 16, "heading_weight": 700},
                "layout": {"section_spacing": "spacious", "radius": 10, "card_style": "elevated", "nav_style": "solid"},
                "animation": {"enabled": True, "speed": 1.2, "intensity": "subtle", "scroll_reveal": "fade",
                              "background_effects": False, "cursor_effects": False}}},
    {"key": "engineer", "name": "Computer Engineer", "tagline": "Blueprint grids, circuit-orange accents, technical type.",
     "design": {"theme": {"mode": "dark", "skin": "engineer"},
                "colors": {"primary": "#0ea5e9", "secondary": "#f97316", "accent": "#22d3ee",
                           "background": "#06182b", "surface": "#0b243d", "text": "#e0f2fe",
                           "background_light": "#f0f9ff", "surface_light": "#ffffff", "text_light": "#0c1a2b"},
                "typography": {"heading_font": "Rajdhani", "body_font": "IBM Plex Sans", "base_size": 16, "heading_weight": 700},
                "layout": {"section_spacing": "comfortable", "radius": 4, "card_style": "outline", "nav_style": "floating"},
                "animation": {"enabled": True, "speed": 1.0, "intensity": "normal", "scroll_reveal": "fade-up",
                              "background_effects": True, "cursor_effects": True}}},
    {"key": "nature", "name": "Nature (Green Lime)", "tagline": "Fresh lime and leaf greens, soft shapes, light and airy.",
     "design": {"theme": {"mode": "light", "skin": "nature"},
                "colors": {"primary": "#4d7c0f", "secondary": "#65a30d", "accent": "#0d9488",
                           "background": "#0b1a0f", "surface": "#12261a", "text": "#ecfccb",
                           "background_light": "#f7fee7", "surface_light": "#ffffff", "text_light": "#14290f"},
                "typography": {"heading_font": "DM Sans", "body_font": "DM Sans", "base_size": 16, "heading_weight": 700},
                "layout": {"section_spacing": "comfortable", "radius": 22, "card_style": "elevated", "nav_style": "floating"},
                "animation": {"enabled": True, "speed": 1.1, "intensity": "subtle", "scroll_reveal": "fade-up",
                              "background_effects": True, "cursor_effects": False}}},
]
PRESET_KEYS = [p_["key"] for p_ in PRESETS]


def preset_designs() -> list[dict]:
    """Presets as full, validated designs (with default sections) for the Design Center."""
    out = []
    for p_ in PRESETS:
        merged = default_design()
        for group, values in p_["design"].items():
            merged[group].update(values)
        out.append({"key": p_["key"], "name": p_["name"], "tagline": p_["tagline"], "design": sanitize(merged)})
    return out
