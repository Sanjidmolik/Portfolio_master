---
name: frontend-design
description: Premium, creative, responsive visual design for the portfolio's public pages - layout, typography, colour, spacing, illustration (custom SVG), section composition and responsive behaviour. Use when building or restyling a page or section, adding a new visual component, changing the look of cards/hero/nav/footer, creating SVG illustrations, fixing "it looks generic/cluttered/off" feedback, or making a design work across mobile, tablet and desktop.
---

# Frontend Design

You are acting as a senior visual designer who also writes production CSS. The goal is a
distinctive, credible portfolio - cinematic and memorable, never a template.

## 1. Learn the project before designing

Always do this first; do not assume a stack.

1. Read `templates/public/base.html`, the relevant `templates/public/sections/*.html`, and
   `static/css/site.css` (sections are delimited by `/* ---------- Name ---------- */` comments).
2. Read `portfolio/design.py`. **All brand values come from CSS custom properties generated
   there** (`--primary`, `--secondary`, `--accent`, `--bg`, `--surface`, `--text`, their `-rgb`
   variants, `--font-heading`, `--font-body`, `--font-mono`, `--radius`, `--container`,
   `--section-space`, `--speed`, `--intensity`). Admins change them in the Design Center.
3. Note body modifier classes: `card-{outline|elevated|solid|glass}`, `nav-{floating|solid|minimal}`,
   `reveal-*`, `transition-*`, `no-motion`, `no-bg-fx`, `no-cursor-fx`. New components must look
   right under every variant.

Current stack: Flask + Jinja templates, one hand-written stylesheet, vanilla JS. **No Tailwind,
no build step.** If you are working in a different project (React/Next.js/Tailwind), apply the
same principles with that project's tokens instead.

## 2. Design direction (this portfolio)

- Identity: "broadcast control room meets code" - ON AIR tally lights, timecode, channel
  numbers (`CH 01`), monitor frames, waveforms, colour bars, terminal snippets. Reuse these motifs;
  invent new ones only if they fit the story (broadcast ops -> software -> security).
- Dark-first (deep navy/charcoal), electric blue/cyan with restrained purple accent.
  Light theme must be equally polished, not an afterthought.
- Gradients: one brand gradient (`--grad`) used sparingly - CTAs, highlighted words, active chips.
  Never more than ~3 gradient elements visible in one viewport.
- Glassmorphism only through the `card-glass` variant; don't hardcode `backdrop-filter` elsewhere.

## 3. Rules for writing styles

- **Never hardcode brand colours, fonts or radii.** Use tokens: `var(--primary)`,
  `rgb(var(--text-rgb) / .64)`, `var(--radius)`. Status colours (success `#34d399`, warning
  `#fbbf24`, error `#f87171`, ON AIR red `#ff3b4e`) are the only fixed hues.
- Derived neutrals: `--muted`, `--faint`, `--line`, `--line-strong`, `--card-bg`. Use them for text
  hierarchy and borders so both themes work automatically.
- Spacing scale: 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 52 / 64 / 80px; vertical rhythm between
  sections is always `var(--section-space)`.
- Type scale: fluid `clamp()` for display sizes (hero `clamp(2.6rem, 6.6vw, 5.4rem)`, section title
  `clamp(2rem, 4.2vw, 3.1rem)`); body 1-1.1rem; mono labels .66-.78rem with letter-spacing .12-.2em.
- Max line length 56-65ch for paragraphs. One `h1` per page; sections use `h2` (via
  `_section_head.html`), cards `h3`/`h4`.
- Layout with CSS grid + `minmax(0, 1fr)` (prevents overflow). Use `auto-fill/minmax()` for card grids.
- Every new section uses the shared head: `{% include "public/_section_head.html" %}` and lives in
  `templates/public/sections/<key>.html` wrapped in `<section class="section ..." id="<key>">`.
- Images: always `width`/`height` attributes, `loading="lazy"` + `decoding="async"` below the fold,
  `object-fit: cover` inside a fixed `aspect-ratio` box. Hero/LCP image gets `fetchpriority="high"`.
- SVG illustrations: inline, `aria-hidden="true"` when decorative, colours via `var(--…)` or
  `currentColor`, `viewBox` sized to the art, unique gradient ids (suffix with an item id in loops).
- Icons: use `{{ icon('name') }}` from `portfolio/icons.py`; add new Lucide-style paths there rather
  than pulling an icon library.

## 4. Responsive behaviour

Breakpoints already in `site.css`: 1080, 960 (nav -> burger, grids -> single column), 720, 480.
Design mobile layouts deliberately:
- Identity (name + role) must be visible in the first mobile viewport.
- Touch targets >= 40x40px; horizontal chip rows scroll instead of wrapping into 4 lines.
- No hover-only information: `@media (hover: none)` must reveal hover content.
- Test at 375, 768, 1024, 1440 widths. Nothing may cause horizontal scroll.

## 5. Workflow

1. Restate the design goal in one sentence and which section/component it touches.
2. Inspect current markup/CSS and identify existing classes to reuse.
3. Sketch the structure (semantic HTML first), then style, then add motion via the
   `animation-motion` skill if needed.
4. Check both themes, all four card styles, and the three nav styles.
5. Verify in the browser at mobile and desktop widths (use the preview server in
   `../.claude/launch.json`, name `portfolio`), and run `pytest` to ensure templates still render.

## 6. Quality checklist

- [ ] Uses design tokens only; switching colours in the Design Center restyles it fully
- [ ] Works in dark and light theme; text contrast >= 4.5:1 (3:1 for large text)
- [ ] Looks intentional under `card-outline/elevated/solid/glass`
- [ ] Responsive at 375/768/1024/1440 with no horizontal overflow
- [ ] Clear visual hierarchy: one focal point per section, consistent section head
- [ ] No placeholder text that reads like a real claim (no fake stats, logos or testimonials)
- [ ] Empty states handled (section hidden or friendly message when content is empty)
- [ ] Images sized, lazy-loaded, no layout shift
- [ ] No new dependencies, fonts or CDNs without explicit justification
