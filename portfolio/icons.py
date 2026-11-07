"""Inline SVG icon set (Lucide-style, stroke based) + skill icon resolver.

Inline icons avoid an icon-font dependency and an extra network request.
"""
from __future__ import annotations

import re

from flask import url_for
from markupsafe import Markup, escape

P = lambda *ds: "".join(f'<path d="{d}"/>' for d in ds)  # noqa: E731

ICONS = {
    "github": P("M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4", "M9 18c-4.51 2-5-2-7-2"),
    "linkedin": P("M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z") + '<rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/>' + P("m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"),
    "x": P("M4 4l11.733 16h4.267l-11.733-16z", "M4 20l6.768-6.768", "M13.232 10.768 20 4"),
    "facebook": P("M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"),
    "instagram": '<rect x="2" y="2" width="20" height="20" rx="5"/>' + P("M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z", "M17.5 6.5h.01"),
    "youtube": P("M2.5 17a24 24 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.6 49.6 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24 24 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.6 49.6 0 0 1-16.2 0A2 2 0 0 1 2.5 17", "m10 15 5-3-5-3z"),
    "globe": '<circle cx="12" cy="12" r="10"/>' + P("M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20", "M2 12h20"),
    "send": P("M14.54 21.69a.5.5 0 0 0 .94-.03l6.5-19a.5.5 0 0 0-.64-.63l-19 6.5a.5.5 0 0 0-.02.93l7.93 3.18a2 2 0 0 1 1.11 1.11z", "m21.85 2.15-10.94 10.94"),
    "phone": P("M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"),
    "map-pin": P("M20 10c0 5-5.54 10.19-7.4 11.8a1 1 0 0 1-1.2 0C9.54 20.19 4 15 4 10a8 8 0 0 1 16 0") + '<circle cx="12" cy="10" r="3"/>',
    "arrow-right": P("M5 12h14", "m12 5 7 7-7 7"),
    "arrow-left": P("M19 12H5", "m12 19-7-7 7-7"),
    "arrow-up-right": P("M7 7h10v10", "M7 17 17 7"),
    "arrow-down": P("M12 5v14", "m19 12-7 7-7-7"),
    "external": P("M15 3h6v6", "M10 14 21 3", "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"),
    "download": P("M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", "m7 10 5 5 5-5", "M12 15V3"),
    "sun": '<circle cx="12" cy="12" r="4"/>' + P("M12 2v2", "M12 20v2", "m4.93 4.93 1.41 1.41", "m17.66 17.66 1.41 1.41", "M2 12h2", "M20 12h2", "m6.34 17.66-1.41 1.41", "m19.07 4.93-1.41 1.41"),
    "moon": P("M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"),
    "menu": P("M4 6h16", "M4 12h16", "M4 18h16"),
    "close": P("M18 6 6 18", "m6 6 12 12"),
    "shield": P("M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z", "m9 12 2 2 4-4"),
    "network": '<rect x="16" y="16" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="9" y="2" width="6" height="6" rx="1"/>' + P("M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3", "M12 12V8"),
    "search": '<circle cx="11" cy="11" r="8"/>' + P("m21 21-4.3-4.3"),
    "fingerprint": P("M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4", "M14 13.12c0 2.38 0 6.38-1 8.88", "M17.29 21.02c.12-.6.43-2.3.5-3.02", "M2 12a10 10 0 0 1 18-6", "M2 16h.01", "M21.8 16c.2-2 .13-5.35 0-6", "M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2", "M8.65 22c.21-.66.45-1.32.57-2", "M9 6.8a6 6 0 0 1 9 5.2v2"),
    "broadcast": P("M4.9 16.1C1 12.2 1 5.8 4.9 1.9", "M7.8 4.7a6.14 6.14 0 0 0-.8 7.5", "M16.2 4.8c2 2 2.26 5.11.8 7.47", "M19.1 1.9a10 10 0 0 1 0 14.1", "M9.5 18h5", "m8 22 4-11 4 11") + '<circle cx="12" cy="9" r="2"/>',
    "monitor": '<rect x="2" y="3" width="20" height="14" rx="2"/>' + P("M8 21h8", "M12 17v4"),
    "playout": '<rect x="2" y="4" width="20" height="16" rx="2"/>' + P("m10 9 5 3-5 3z", "M2 8h20"),
    "signal": P("M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"),
    "api": P("M8 3H7a2 2 0 0 0-2 2v5a2 2 0 0 1-2 2 2 2 0 0 1 2 2v5c0 1.1.9 2 2 2h1", "M16 21h1a2 2 0 0 0 2-2v-5c0-1.1.9-2 2-2a2 2 0 0 1-2-2V5a2 2 0 0 0-2-2h-1"),
    "code": P("m16 18 6-6-6-6", "m8 6-6 6 6 6"),
    "terminal": P("m4 17 6-6-6-6", "M12 19h8"),
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2"/>' + P("M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"),
    "graduation": P("M21.42 10.92a1 1 0 0 0-.02-1.84L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.83l8.57 3.91a2 2 0 0 0 1.66 0z", "M22 10v6", "M6 12.5V16a6 3 0 0 0 12 0v-3.5"),
    "award": '<circle cx="12" cy="8" r="6"/>' + P("M15.48 12.89 17 22l-5-3-5 3 1.52-9.11"),
    "certificate": '<rect x="3" y="4" width="18" height="12" rx="2"/>' + P("M7 8h10", "M7 12h5", "m14 16 1.5 5 1.5-1.5 1.5 1.5L20 16"),
    "star": P("M11.52 2.3a.53.53 0 0 1 .95 0l2.31 4.68a2.12 2.12 0 0 0 1.6 1.16l5.16.76a.53.53 0 0 1 .3.9l-3.74 3.64a2.12 2.12 0 0 0-.61 1.88l.88 5.14a.53.53 0 0 1-.77.56l-4.62-2.43a2.12 2.12 0 0 0-1.97 0L6.4 21.01a.53.53 0 0 1-.77-.56l.88-5.14a2.12 2.12 0 0 0-.61-1.88L2.16 9.8a.53.53 0 0 1 .3-.9l5.16-.76a2.12 2.12 0 0 0 1.6-1.16z"),
    "fork": '<circle cx="12" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/>' + P("M18 9v2c0 .6-.4 1-1 1H7c-.6 0-1-.4-1-1V9", "M12 12v3"),
    "repo": P("M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"),
    "users": P("M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", "M22 21v-2a4 4 0 0 0-3-3.87", "M16 3.13a4 4 0 0 1 0 7.75") + '<circle cx="9" cy="7" r="4"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/>' + P("M16 2v4", "M8 2v4", "M3 10h18"),
    "clock": '<circle cx="12" cy="12" r="10"/>' + P("M12 6v6l4 2"),
    "check": P("M20 6 9 17l-5-5"),
    "home": P("M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8", "M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"),
    "play": P("M6 3.5v17a1 1 0 0 0 1.5.86l14.5-8.5a1 1 0 0 0 0-1.72L7.5 2.64A1 1 0 0 0 6 3.5z"),
    "chevrons-down": P("m7 6 5 5 5-5", "m7 13 5 5 5-5"),
    "tv": '<rect x="2" y="7" width="20" height="15" rx="2"/>' + P("m17 2-5 5-5-5"),
    "copy": '<rect x="8" y="8" width="14" height="14" rx="2"/>' + P("M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"),
    "sparkles": P("M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0L14.06 8.5A2 2 0 0 0 15.5 9.94l6.14 1.58a.5.5 0 0 1 0 .96L15.5 14.06a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z", "M20 3v4", "M22 5h-4"),
    "layers": P("m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z", "m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65", "m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"),
    "dashboard": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "user": '<circle cx="12" cy="8" r="5"/>' + P("M20 21a8 8 0 0 0-16 0"),
    "folder": P("M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"),
    "palette": '<circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/>' + P("M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.65-.75 1.65-1.69 0-.44-.18-.84-.44-1.13-.29-.29-.44-.65-.44-1.13a1.64 1.64 0 0 1 1.67-1.67h2c3.05 0 5.56-2.5 5.56-5.55C21.97 6.01 17.46 2 12 2z"),
    "inbox": P("M22 12h-6l-2 3h-4l-2-3H2", "M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"),
    "settings": '<circle cx="12" cy="12" r="3"/>' + P("M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"),
    "logout": P("M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", "m16 17 5-5-5-5", "M21 12H9"),
    "eye": P("M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-19.88 0") + '<circle cx="12" cy="12" r="3"/>',
    "eye-off": P("M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68", "M6.61 6.61A13.53 13.53 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61", "M14.12 14.12a3 3 0 1 1-4.24-4.24", "m2 2 20 20"),
    "grip": '<circle cx="9" cy="12" r="1"/><circle cx="9" cy="5" r="1"/><circle cx="9" cy="19" r="1"/><circle cx="15" cy="12" r="1"/><circle cx="15" cy="5" r="1"/><circle cx="15" cy="19" r="1"/>',
    "plus": P("M5 12h14", "M12 5v14"),
    "pencil": P("M21.17 6.81a1 1 0 0 0-3.99-3.99L3.84 16.17a2 2 0 0 0-.5.83l-1.32 4.35a.5.5 0 0 0 .62.62l4.35-1.32a2 2 0 0 0 .83-.5z", "m15 5 4 4"),
    "trash": P("M3 6h18", "M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6", "M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"),
    "chevron-up": P("m18 15-6-6-6 6"),
    "chevron-down": P("m6 9 6 6 6-6"),
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/>' + P("m21 15-3.09-3.09a2 2 0 0 0-2.82 0L6 21"),
    "file": P("M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z", "M14 2v4a2 2 0 0 0 2 2h4", "M10 9H8", "M16 13H8", "M16 17H8"),
    "link": P("M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71", "M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"),
    "refresh": P("M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8", "M21 3v5h-5", "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16", "M8 16H3v5"),
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/>' + P("M7 11V7a5 5 0 0 1 10 0v4"),
    "motion": P("M5 12h.01", "M9 12h.01", "M13 12a4 4 0 1 0 8 0 4 4 0 1 0-8 0"),
    "milestone": '<circle cx="12" cy="12" r="3"/>' + P("M12 2v4", "M12 18v4"),
    "development": P("m16 18 6-6-6-6", "m8 6-6 6 6 6"),
    "security": P("M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"),
    "education": P("M21.42 10.92a1 1 0 0 0-.02-1.84L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.83l8.57 3.91a2 2 0 0 0 1.66 0z", "M22 10v6", "M6 12.5V16a6 3 0 0 0 12 0v-3.5"),
}
ICONS["email"] = ICONS["mail"]
ICONS["twitter"] = ICONS["x"]
ICONS["website"] = ICONS["globe"]
ICONS["telegram"] = ICONS["send"]
ICONS["whatsapp"] = ICONS["phone"]

BUILTIN_SKILL_ICONS = sorted(ICONS.keys())
SLUG_RE = re.compile(r"^[a-z0-9]{1,40}$")


def icon_svg(name: str, cls: str = "icon", size: int | None = None, label: str | None = None) -> Markup:
    body = ICONS.get(name) or ICONS["sparkles"]
    attrs = f'class="{escape(cls)}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'
    if size:
        attrs += f' width="{int(size)}" height="{int(size)}"'
    attrs += f' role="img" aria-label="{escape(label)}"' if label else ' aria-hidden="true" focusable="false"'
    return Markup(f"<svg {attrs}>{body}</svg>")


def skill_icon(skill) -> Markup:
    """Uploaded image > Simple Icons brand logo > built-in icon > monogram."""
    alt = escape(skill.name)
    if getattr(skill, "icon_image", ""):
        return Markup(f'<img src="{url_for("static", filename=skill.icon_image)}" alt="" '
                      f'width="28" height="28" loading="lazy" decoding="async">')
    icon = (skill.icon or "").strip()
    if icon.startswith("si:") and SLUG_RE.match(icon[3:]):
        # Rendered as a CSS mask so every brand logo is tinted with the theme gradient.
        return Markup(f'<span class="si-mask" aria-hidden="true" '
                      f'style="--si:url(https://cdn.simpleicons.org/{icon[3:]})"></span>')
    if icon in ICONS:
        return icon_svg(icon, "icon skill-svg")
    return Markup(f'<span class="monogram">{alt[:2]}</span>')


def any_icon(value: str, cls: str = "icon") -> Markup:
    """Render a built-in icon key or an si:<slug> brand logo (used for editable chips/cards)."""
    value = (value or "").strip()
    if value.startswith("si:") and SLUG_RE.match(value[3:]):
        return Markup(f'<span class="si-mask" aria-hidden="true" '
                      f'style="--si:url(https://cdn.simpleicons.org/{value[3:]})"></span>')
    if value in ICONS:
        return icon_svg(value, cls)
    return Markup("")
