---
name: animation-motion
description: Motion design and implementation - scroll-triggered reveals, hero/intro sequences, hover and cursor interactions, page transitions, loaders, SVG animation, and GSAP / Framer Motion (Motion) usage where the stack supports it - with strict 60fps performance and reduced-motion accessibility. Use when adding or changing any animation, transition or interactive effect, when something feels janky or laggy, or when wiring animation to the Design Center motion settings.
---

# Animation & Motion

Motion must explain, guide or delight - never decorate for its own sake - and it must never
cost usability, performance or accessibility.

## 1. Choose the right tool for the stack

Inspect `requirements.txt` / `package.json` first.

- **This project (Flask + vanilla JS, no bundler):** use CSS transitions/keyframes and the small
  helpers in `static/js/site.js` (IntersectionObserver reveals, rAF pointer effects). Do **not**
  add GSAP or Motion for something CSS can do. Adding a library requires a written reason
  (e.g. complex timeline sequencing or scroll-scrubbed pinning) and must be self-hosted under
  `static/`, loaded `defer`, and allowed by the CSP in `portfolio/__init__.py`.
- **React/Next.js projects:** Motion (`motion/react`) for component/state and layout animation,
  `AnimatePresence` for exit/route transitions, `useReducedMotion()` everywhere. GSAP +
  ScrollTrigger only for scroll-scrubbed or pinned storytelling; create in `useGSAP()` /
  `gsap.context()` and revert on unmount; register plugins once; dynamic-import on the client.
- Lottie only for designer-made illustrations; Three.js only when 3D carries meaning - never
  for background decoration.

## 2. Project motion system (respect it)

- Durations/delays scale with `var(--speed)` (Design Center "Animation speed"); distances and glow
  with `var(--intensity)`. Use the existing tokens: `--t-fast` (180ms), `--t` (420ms),
  `--t-slow` (900ms), `--shift`, `--ease` (`cubic-bezier(.22,1,.36,1)`), `--ease-spring`.
- Kill switches: `html.reduce-motion` (OS setting or visitor pause button, stored as `pf-motion`)
  and `body.no-motion` (admin disabled animations). The global rules at the end of `site.css` zero
  out durations; **any element hidden for an entrance animation must also be forced visible
  there** (see the `.hero-in`, `[data-reveal]`, `.char` rules).
- JS effects must call `motionOK()` before animating and do nothing when it is false.
- Scroll reveals: add `data-reveal` (+ `style="--i:N"` for stagger, N <= 5). Variants come from
  `body.reveal-{fade-up,fade,zoom,slide,none}` - don't hardcode a reveal style per element.
- Entrance sequences start on `body.is-loaded`, not on page load directly.
- New Design Center options: add to `DEFAULT_DESIGN`/`CHOICES` in `portfolio/design.py`, expose a
  body class or CSS var in `body_classes()`/`css_variables()`, add the control in
  `templates/admin/design.html`, and update the preview handler class regex in `site.js`.

## 3. Performance rules

- Animate only `transform` and `opacity` (and `filter` on small elements, briefly). Never animate
  `width/height/top/left/margin/box-shadow` on large or many elements.
- Pointer/scroll handlers: `{ passive: true }`, batch work in `requestAnimationFrame`, read layout
  once then write (no read/write thrash), and stop rAF loops when idle (see `glowLoop`).
- Use IntersectionObserver, not scroll listeners, for "in view" logic; `unobserve` after reveal.
- `will-change` only on a few long-running animated elements; never on lists.
- Avoid large blurred elements (`filter: blur`) - use radial gradients instead.
- Infinite animations: low-frequency, small areas, paused under reduced motion.
- Pointer effects only on `(hover: hover) and (pointer: fine)`.
- Loaders never block content longer than ~1.1s and never depend on the `load` event.
- Budget: no long tasks > 50ms from animation code; Lighthouse performance >= 90 on mobile.

## 4. Accessibility rules

- `prefers-reduced-motion: reduce` -> no parallax, no auto-moving content, no large translations;
  fades <= 200ms are acceptable. Content must be fully visible without JS (`<noscript>` rule in
  `base.html`).
- Nothing flashes more than 3 times per second.
- Auto-rotating text (hero rotator) keeps an `sr-only` full list and `aria-live="off"`.
- Animated content never traps focus or moves interactive targets while the user aims.

## 5. Workflow

1. State the purpose of the motion (orient, focus, feedback, delight) and its trigger.
2. Pick the lightest tool (CSS > vanilla JS > library).
3. Implement using the project tokens; wire `--speed`/`--intensity`.
4. Add reduced-motion / `no-motion` handling in the same change.
5. Test: Design Center with animations off, speed 0.5x and 2x, intensity subtle/bold; OS
   reduced-motion; mobile; DevTools Performance recording (no dropped frames, no layout shifts).

## 6. Quality checklist

- [ ] Purpose is clear; motion is consistent with existing easing and timing
- [ ] Only transform/opacity animated; 60fps on a mid-range phone
- [ ] Honors `--speed`, `--intensity`, `reduce-motion`, `no-motion`, `no-bg-fx`, `no-cursor-fx`
- [ ] Content visible with JS disabled and with reduced motion
- [ ] No new dependency (or a justified, self-hosted, CSP-allowed one)
- [ ] No CLS introduced; loader dismisses promptly
- [ ] Live preview in Design Center still reflects the change
