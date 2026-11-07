---
name: code-review
description: Code review, debugging, refactoring and regression prevention for this portfolio - correctness bugs, root-cause debugging, performance (queries, rendering, JS, assets), maintainability, test coverage and safe refactors. Use when reviewing a change or file, investigating a bug, error, failing test or "it doesn't work", refactoring or cleaning up code, optimising performance, or before declaring a task complete.
---

# Code Review & Debugging

Find real defects, explain them with evidence, fix them with the smallest safe change, and
lock them in with a test. Style nitpicks come last and only if they matter.

## 1. Orient

- Identify the scope: a diff, specific files, a bug report, or a failing test.
- Read the code *and its callers*. For this project the key seams are: route -> context
  processor (`public.inject_globals`) -> template; admin `RESOURCES` registry -> `apply_form` ->
  `admin/_fields.html`; design JSON -> `design.sanitize` -> `css_variables` -> `base.html` and the
  live-preview `postMessage` handler in `site.js`.
- Run the suite first to get a baseline: `.venv/Scripts/python -m pytest -q`.

## 2. Debugging method

1. **Reproduce** - smallest input that fails (Flask test client, browser preview `portfolio`,
   or a pytest case). No fix without a reproduction.
2. **Read the evidence** - full traceback, server logs (`preview_logs`), browser console and
   network panel. Note the first point where reality diverges from expectation.
3. **Hypothesise and test one cause at a time**; don't change several things at once.
4. **Fix the root cause**, not the symptom (e.g. fix the query, not the template that hides
   the error).
5. **Add a regression test** that fails before and passes after.
6. Check for the same bug pattern elsewhere (`Grep`).

Known gotchas here: Jinja macros imported without context can't see context-processor vars
(`icon`/`skill_icon` are registered as globals for this reason); inline `on*=` handlers are
blocked by CSP; `db.create_all()` doesn't alter existing tables; screenshots from a hidden
preview pane can show stale frames - confirm with `javascript_tool` before "fixing" rendering.

## 3. What to look for (priority order)

1. **Correctness** - wrong logic, unhandled `None`/empty states, off-by-one in ordering,
   transactions committed half-way, autoflush of invalid objects, broken redirects, race
   conditions in JS (double submit, stale closures).
2. **Security** - defer to the `security-review` skill for anything auth/input/upload related.
3. **Regressions** - did the change break another section, theme, card style, the admin preview,
   reduced-motion behaviour, or mobile layout?
4. **Performance** - N+1 queries (counts in loops, lazy relationships in templates), repeated
   work per request in context processors, unbounded queries, large unoptimised images, layout
   thrash or unthrottled handlers in JS, render-blocking assets.
5. **Maintainability** - duplication that should use an existing helper (`RESOURCES`,
   `render_field`, `_section_head.html`, `icon()`), unclear names, functions doing several
   jobs, dead code, magic values that belong in config/design tokens.
6. **Tests** - missing coverage for new branches, assertions too weak to catch regressions.

## 4. Refactoring rules

- Refactor only with a green test suite; add characterization tests first if coverage is thin.
- Behaviour-preserving steps, one concern per change; never mix refactor + feature in one step.
- Keep public URLs, template block names, CSS hooks (`data-*` attributes used by JS) and
  design JSON keys stable - stored data and the Design Center depend on them.
- Delete code only after confirming no references (`Grep` templates, JS and Python).

## 5. Performance checks

- Python: count queries per page (SQLAlchemy echo or event listener in a quick test); keep
  the home page under ~20 queries; cache external calls (`Setting` cache pattern).
- Frontend: images have dimensions and lazy loading; JS deferred; no long tasks; Lighthouse
  mobile >= 90 performance / >= 95 accessibility as a target.

## 6. Review output format

Group by severity; each item: `file:line` - problem - why it matters (concrete failure
scenario) - suggested fix. Then "Verified": what you ran (tests, browser checks) and the result.
State plainly what you did not verify.

## 7. Definition of done

- [ ] Bug reproduced, root cause identified and explained
- [ ] Minimal fix applied; no unrelated changes
- [ ] Regression test added; full `pytest` suite green
- [ ] Checked in the running app when UI is affected (desktop + mobile, both themes)
- [ ] No new console errors or server errors in logs
- [ ] Similar occurrences searched and handled
