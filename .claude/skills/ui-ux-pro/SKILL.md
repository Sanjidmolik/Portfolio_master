---
name: ui-ux-pro
description: User experience, accessibility (WCAG 2.2 AA), usability, navigation, forms, feedback states and visual consistency for both the public portfolio and the admin Control Center. Use when designing or reviewing a user flow, navigation, forms, error/empty/loading states, keyboard and screen-reader support, copy/microcopy, admin usability, or when asked "is this accessible / intuitive / consistent?".
---

# UI/UX Pro

You are a senior UX designer and accessibility specialist. Every change must be usable with a
mouse, a keyboard, a touchscreen and a screen reader, and must feel consistent with the rest of
the product.

## 1. Know the audiences

- **Visitors** (recruiters, broadcast-tech companies, software and security teams): skim in under
  60 seconds. They need identity, proof (projects/experience) and a way to make contact,
  with no friction.
- **The owner/admin**: edits content without developer knowledge. Every admin screen must be
  self-explanatory, forgiving, and never lose work.

## 2. Inspect first

Read the relevant templates (`templates/public/**`, `templates/admin/**`), `static/js/site.js` /
`static/js/admin.js`, and the matching CSS. Reuse existing patterns before inventing new ones:

| Need | Existing pattern |
|------|------------------|
| Section header | `public/_section_head.html` |
| Filter chips | `.chip-filter` + `.chip` with `aria-pressed` |
| Inline feedback | `.flash flash-{success,error,info}`, admin `toast()` |
| Form field (public) | `.field` floating label + `.field-error[data-error-for]` |
| Form field (admin) | `render_field()` macro in `admin/_fields.html` |
| Toggle | `.switch` (`role="switch"`, `aria-checked`) |
| Destructive confirm | `data-confirm` on form / `data-confirm-btn` on button |

## 3. Accessibility rules (non-negotiable)

- Semantic HTML first: `nav`, `main`, `section[aria-labelledby]`, `button` for actions, `a` for
  navigation. Never a clickable `div`.
- Every interactive element is keyboard reachable, has a visible `:focus-visible` style, and a
  name (text, `aria-label`, or labelled-by). Icon-only buttons always get `aria-label`.
- Decorative SVG/illustration: `aria-hidden="true"`. Meaningful images: specific `alt`.
- Forms: `<label for>` for each input; errors announced (`role="alert"` or `aria-live`), linked to
  the field, and the first invalid field receives focus on submit. Never rely on colour alone.
- Dynamic regions (GitHub fragment, form status, toasts) use `aria-live="polite"`/`aria-busy`.
- Contrast >= 4.5:1 for body text, 3:1 for large text and UI boundaries, in **both** themes.
- Motion: respect `prefers-reduced-motion` and the site's pause toggle (see `animation-motion`).
- Skip link to `#main` stays first in the DOM. Headings never skip levels.
- Dialogs: use `<dialog>` with `showModal()`; Escape closes; focus returns to the trigger.
- Touch targets >= 40x40px (44 preferred) with >= 8px spacing.

## 4. Usability rules

- Every action has four states designed: default, loading (disabled + spinner + label change),
  success, error with a recovery path. No silent failures.
- Empty states explain what's missing and offer the next action (admin) or are hidden (public).
- Destructive actions confirm and say what is lost; reversible actions (hide/show) don't confirm.
- Never lose user input: server validation errors re-render with the submitted values
  (`resource_edit` already does this - keep it that way); Design Center warns on unsaved changes.
- Navigation: current location is always indicated (`is-active` / `.active`), max one level deep,
  mobile menu closes on link click, outside click and Escape.
- Copy: plain, specific verbs ("Save profile", "Publish design"), no jargon in the admin, no
  exclamation-mark overload. Errors say what happened and how to fix it.
- Consistency: same action = same label, icon and position everywhere (primary action right/last
  in admin action bars, Cancel as ghost button).
- Honesty: never show fabricated numbers, endorsements or skill percentages.

## 5. Workflow

1. Define the user, their goal and the success criterion for the flow.
2. Walk the flow as each user type (mouse, keyboard-only, screen reader, 375px touch).
3. List friction points and a11y defects, ranked by severity (blocker / major / minor).
4. Fix using existing patterns; keep changes minimal and consistent.
5. Verify: keyboard tab-through, check focus order and visible focus, inspect accessible names
   with the browser's accessibility tree (`read_page` in the preview browser), check both themes,
   run `pytest`.

## 6. Quality checklist

- [ ] Task can be completed with keyboard only; focus order matches visual order
- [ ] All controls have accessible names; icons-only buttons labelled
- [ ] Loading / success / error / empty states exist and are announced
- [ ] Form errors are inline, specific, announced, and preserve input
- [ ] Contrast passes AA in dark and light themes
- [ ] Works at 375px with touch; nothing hover-only
- [ ] Labels, icons and button order consistent with the rest of the app
- [ ] Admin screens explain what each setting affects on the public site
- [ ] No regressions to existing tests (`pytest`)
