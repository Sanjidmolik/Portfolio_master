"""Dynamically rendered Open Graph image (1200x630 PNG) using Pillow."""
from __future__ import annotations

import io
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _font(size, bold=False):
    candidates = (["arialbd.ttf", "DejaVuSans-Bold.ttf", "segoeuib.ttf"] if bold
                  else ["arial.ttf", "DejaVuSans.ttf", "segoeui.ttf"])
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


@lru_cache(maxsize=8)
def _render(name, headline, bg, primary, secondary, accent, text):
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), _rgb(bg))
    d = ImageDraw.Draw(img)
    # grid
    for x in range(0, W, 48):
        d.line([(x, 0), (x, H)], fill=tuple(min(255, c + 10) for c in _rgb(bg)), width=1)
    for y in range(0, H, 48):
        d.line([(0, y), (W, y)], fill=tuple(min(255, c + 10) for c in _rgb(bg)), width=1)
    # signal waveform
    import math
    pts = [(x, 470 + math.sin(x / 38) * 26 * math.sin(x / 210)) for x in range(0, W + 1, 4)]
    d.line(pts, fill=_rgb(secondary), width=4)
    # accent bars (like a broadcast colour bar)
    for i, col in enumerate((primary, secondary, accent)):
        d.rectangle([80 + i * 56, 96, 80 + i * 56 + 44, 104], fill=_rgb(col))
    d.text((80, 140), "ON AIR", font=_font(26, True), fill=_rgb(secondary))
    d.text((80, 200), name or "Portfolio", font=_font(68, True), fill=_rgb(text))
    d.text((80, 300), headline or "", font=_font(32), fill=tuple(int(c * 0.75) for c in _rgb(text)))
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def render_og(name, headline, colors) -> bytes:
    return _render(name or "", (headline or "")[:70], colors["background"], colors["primary"],
                   colors["secondary"], colors["accent"], colors["text"])
