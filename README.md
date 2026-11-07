# Sanjidur Rahman Sanjid: Portfolio

A cinematic, animated developer portfolio with a private **Control Center** (admin CMS)
to edit every piece of content and the whole visual design without touching code.

Built with **Flask + SQLAlchemy** (SQLite for development, PostgreSQL for production),
server-rendered Jinja templates, and dependency-free vanilla JS/CSS animations.

## Features

**Public site**
- Animated hero: letter-by-letter name reveal, rotating titles, live "ON AIR" timecode,
  broadcast-monitor SVG illustration with radar rings, waveform and floating tech chips
- About section with focus pillars and an interactive, filterable career-journey timeline
- Experience timeline (company, role, dates, responsibilities, achievements, tech, logo)
- "Technology Arsenal": filterable skill cards with tilt and spotlight effects. Proficiency is optional, with no percentages
- Featured projects plus an archive page with a tech filter and case-study pages with a gallery lightbox
- Education, certifications and awards
- GitHub activity: profile, stats, contribution heatmap, languages and top repos. Fetched
  server-side, cached in the DB, and degrades gracefully
- Contact form with validation, honeypot, rate limiting, AJAX loading/success/error states,
  and optional SMTP email notification
- Dark/light/system themes, visitor theme toggle, animation pause toggle, `prefers-reduced-motion`
- SEO: per-page meta, Open Graph image (generated), JSON-LD, `sitemap.xml`, `robots.txt`

**Control Center (`/admin`)**
- Dashboard: counts, configuration checklist, recent messages, quick actions
- Profile: name, titles, intro, about, goals, photo, CV (PDF), contact details, GitHub username, SEO
- Manage projects (with screenshot gallery), skills, experience, journey milestones, education,
  certifications/awards and social links: add, edit, delete, drag-to-reorder, show/hide, feature
- Messages inbox
- **Design Center**: theme, colour system (with presets and a contrast check), fonts, sizes,
  layout, card/nav style, animation speed/intensity/effects, and section order, visibility and titles.
  It has a **live preview** (desktop/tablet/mobile) plus *Save draft*, *Preview changes*, *Publish*,
  *Reset to default* and *Discard draft*. Published settings drive the real public site.

## Quick start (development)

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
```

Edit `.env` and set `SECRET_KEY`, plus `ADMIN_USERNAME` / `ADMIN_PASSWORD` for the first admin
(at least 12 characters, mixed case and a number). Then run:

```bash
flask --app app run --debug
```

Open http://localhost:5000, then sign in at http://localhost:5000/admin.
The database and initial content are created automatically on first start.

Prefer not to keep a password in `.env`? Leave those blank and create the admin interactively:

```bash
flask --app app create-admin
```

Other commands: `flask --app app reset-admin-password`, `flask --app app github-refresh`,
`flask --app app init-db`.

## First steps after signing in

Initial content uses only facts from the original site and your brief. Anything that
needs your confirmation was created as a **hidden draft**:

1. **Skills**: all 21 starter skills are hidden. Switch on the ones you want to show.
2. **Experience / Education**: replace "Company name (edit me)" / "University name (edit me)",
   add dates, then make them visible.
3. **Career Journey**: add years to the hidden milestones and publish them.
4. **Profile**: upload a photo and CV, add your public email and GitHub username.
5. **Social Links**: add LinkedIn, GitHub, email, etc.
6. **Projects → CyberQuest**: add screenshots plus GitHub/demo links (buttons only appear when a link is set), and confirm the status.

## Security

- No hardcoded credentials or secret key. Production refuses to start without `SECRET_KEY`.
- Passwords hashed with scrypt; constant-time-ish failed logins; session fixation protection;
  sessions expire (8 h default) and are revoked on password change or "sign out everywhere".
- Every `/admin` route is protected server-side; admin JSON APIs return 401 to anonymous users.
- CSRF protection on every POST (forms and fetch), plus login (5/min) and contact-form rate limits.
- Strict Content-Security-Policy with nonces, `X-Frame-Options`, `nosniff`, HSTS in production,
  and `no-store` / `noindex` on admin pages.
- Uploads: images are verified and **re-encoded to WebP** (strips metadata and payloads, no SVG),
  CVs must be real PDFs, random filenames, size limits.
- Design settings are validated against whitelists before being written into CSS.
- The GitHub token (optional) is used only server-side.

## Production deployment

1. Set `APP_ENV=production`, a strong `SECRET_KEY`, `DATABASE_URL` (PostgreSQL), `SITE_URL`,
   and `TRUST_PROXY=1` when behind a proxy/load balancer.
2. `pip install -r requirements.txt`
3. Run `gunicorn app:app` (Linux, see `Procfile`) or `waitress-serve --port 8000 app:app` (Windows).
4. Persist `static/uploads/` (a mounted disk or volume) so uploaded images survive redeploys.
5. With several workers, set `RATELIMIT_STORAGE_URI` to Redis so rate limits are shared.

## Tests

```bash
pytest
```

The tests cover auth, authorization, CSRF, rate limiting, CRUD, upload validation, design
draft/preview/publish, the contact form, XSS escaping and the GitHub fallbacks.

## Project structure

```
app.py                 entry point
portfolio/
  __init__.py          app factory, security headers, error pages
  config.py            environment-driven configuration
  models.py            database models
  auth.py              login/logout, session validation, login_required
  admin.py             Control Center routes + generic CRUD registry
  public.py            public routes, contact form, SEO endpoints
  design.py            design defaults, validation, CSS variable generation
  github.py            cached GitHub API integration
  uploads.py           secure image/PDF handling
  icons.py, og.py      inline SVG icons, Open Graph image
  seed.py, cli.py      initial content, management commands
templates/public/      site layout, sections, project pages
templates/admin/       Control Center screens
static/css, static/js  site + admin styles and scripts
tests/                 pytest suite
```
