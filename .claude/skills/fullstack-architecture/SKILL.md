---
name: fullstack-architecture
description: Architecture and implementation of features end to end - data models, migrations, backend routes/APIs, server-rendered or React/Next.js frontends, TypeScript typing, configuration, caching and project structure - with an emphasis on maintainable, testable production code. Use when adding a new feature or content type, designing an API or database schema, deciding where code belongs, planning a refactor or stack migration, integrating an external service, or preparing for deployment.
---

# Full-Stack Architecture

Design features that fit the existing system, are easy to change later, and are covered by
tests. Prefer extending established patterns over introducing new ones.

## 1. Establish the real stack first

Read `requirements.txt` (and `package.json` if present), `app.py`, and `portfolio/__init__.py`.
**Current stack:** Flask 3 app factory, Flask-SQLAlchemy 3 / SQLAlchemy 2 (SQLite dev, PostgreSQL
prod via `DATABASE_URL`), Flask-WTF CSRF, Flask-Limiter, Jinja templates, vanilla JS, pytest.
No Node toolchain.

Do **not** migrate to React/Next.js/TypeScript unless the user asks or a requirement truly
cannot be met; if proposing it, write the trade-offs (hosting, auth rewrite, data migration,
effort) and get approval first.

## 2. Map of the codebase

| Concern | Location |
|---------|----------|
| Config (env-driven, no secrets in code) | `portfolio/config.py`, `.env.example` |
| Models | `portfolio/models.py` (`OrderedMixin` gives `sort_order`, `visible`, timestamps, `published()`, `ordered()`) |
| Public routes / SEO / contact | `portfolio/public.py` (context processor injects profile, design, `available` sections) |
| Admin + generic CRUD | `portfolio/admin.py` - `RESOURCES` registry of `Resource`/`Field` |
| Auth | `portfolio/auth.py` (`login_required`, `current_admin`) |
| Design system | `portfolio/design.py` (defaults, `sanitize`, CSS vars, draft/publish) |
| Uploads | `portfolio/uploads.py` (`save_image`, `save_pdf`, `delete_upload`) |
| External API + cache | `portfolio/github.py` (cache in `Setting` table) |
| Seeds / CLI | `portfolio/seed.py`, `portfolio/cli.py` |
| Tests | `tests/conftest.py` fixtures `app`, `client`, `admin_client`, helpers `admin_token`, `png_bytes` |

## 3. Recipes

**New editable content type (e.g. "Talks")**
1. Model in `models.py` inheriting `OrderedMixin`; explicit `String(n)` lengths; helper
   properties for parsed lists (`split_lines`, `split_tags`).
2. Register a `Resource` in `RESOURCES` with typed `Field`s - you get list/create/edit/delete/
   toggle/reorder/upload screens for free. Only write custom routes for behaviour the generic CRUD
   can't express.
3. Public section: `templates/public/sections/<key>.html`, add key to `SECTION_KEYS` and
   `DEFAULT_SECTIONS` in `design.py`, add an `available[...]` rule and context query in `public.py`.
4. Tests: admin create -> public render, hidden item not public, validation failure (422).

**Schema changes:** `db.create_all()` only creates missing tables - it does not alter columns. For
a column change on an existing deployment, add Flask-Migrate/Alembic (ask first) or provide an
explicit, idempotent migration command in `cli.py`. Never silently drop data.

**APIs:** JSON endpoints return `{"ok": bool, ...}` with proper status codes (400 invalid,
401 unauthenticated, 404, 422 validation, 429). Validate input server-side with whitelists; never
trust client-side checks. Admin APIs live under `/admin` so `before_request` auth applies.

**External services:** call server-side only, timeouts on every request (<= 10s), cache results
in `Setting`, back off on failure, render a graceful fallback, never raise into a template.

## 4. Standards

- Python: type hints on public functions, small pure helpers, no logic in templates beyond
  presentation, `db.session.get()` (not `Query.get`), commit once per request action.
- No N+1 queries in loops over collections that can grow; use `published()` / joined loading.
- Config only via env vars; add every new variable to `.env.example` with a comment.
- Secrets never reach templates or JS. Feature flags and settings go through `Setting`/design JSON,
  never `localStorage` as source of truth.
- Errors: user-facing messages via `flash()`/JSON, details to `current_app.logger`.
- If working in a React/Next.js/TypeScript project: strict TS, server components by default,
  data access in server-only modules, Zod (or equivalent) schemas shared by API and forms,
  route handlers for mutations with auth checks inside the handler, no `any`.

## 5. Workflow

1. Clarify the requirement and acceptance criteria; identify affected layers.
2. Find the closest existing pattern and reuse it; write a short plan (models -> routes ->
   templates -> tests) before coding when more than ~3 files change.
3. Implement in thin vertical slices; keep diffs focused.
4. Write/extend pytest tests alongside the change; run `.venv/Scripts/python -m pytest -q`.
5. Verify in the running app (preview server `portfolio`), including the admin flow.
6. Update `README.md` / `.env.example` if setup or config changed.

## 6. Quality checklist

- [ ] Fits existing structure; no duplicated patterns or parallel abstractions
- [ ] Server-side validation and authorization for every write path
- [ ] Works on SQLite and PostgreSQL (no dialect-specific SQL)
- [ ] Migrations/data safety considered for existing databases
- [ ] Graceful degradation for external services
- [ ] Tests added and full suite green
- [ ] No unnecessary dependencies; new ones pinned in `requirements.txt` with justification
- [ ] Docs and `.env.example` updated
