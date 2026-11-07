# Portfolio Audit Report

**Project:** Sanjidur Rahman Sanjid – Portfolio & Control Center
**Audit date:** 7 November 2026
**Scope:** whole repository (`my_portfolio-master/`): application code, templates, static assets, configuration, dependencies, tests, and readiness for publishing to GitHub.
**Stack:** Python 3.13 · Flask 3.1 · SQLAlchemy 2.1 · Flask-WTF (CSRF) · Flask-Limiter · Pillow · Jinja templates · vanilla JS/CSS

---

## 1. Verdict

| Area | Result |
|---|---|
| Security | **Pass**: no critical or high-severity issues. 4 issues found and **fixed** during the audit (see §4). |
| GitHub upload readiness | **Certified ready**: no secrets, credentials, databases, uploads or private personal data in the files that would be committed (see §5). |
| Functionality | **Pass**: 46/46 automated tests, 0 broken internal links, 0 automated accessibility errors, no browser console errors. |
| Dependencies | **Pass**: no known vulnerabilities in pinned application dependencies (pip-audit / PyPI advisory database). |

> **Two actions for you** (cannot be done automatically):
> 1. **Restart the server you run on port 5055.** It is still running code from before today's fixes.
> 2. **Remove the `ADMIN_PASSWORD=` line from `.env`** once you have changed your password in **Admin → Security**. It is only needed to create the first admin account.

---

## 2. Method

| Check | Tool / approach | Result |
|---|---|---|
| Static security analysis (Python) | `bandit 1.9` on `portfolio/` and `app.py` (2,776 lines) | 0 high · 6 medium · 1 low, **all reviewed; false positives** (§4, F8) |
| Dependency vulnerabilities | `pip-audit` on `requirements.txt` and the installed `.venv` | 0 in app dependencies; 1 in the `pip` tool itself → **fixed** |
| Secrets & private-data scan | Pattern scan of every file that would be committed: real `.env` values, API-token formats (GitHub, AWS, OpenAI, Slack, private keys), password assignments, phone numbers, addresses, family names | 1 issue → **fixed** (F1) |
| Git publish simulation | `git ls-files --others --exclude-standard` against a throw-away bare repo (no `.git` created in the project) | 70 files would be committed; all sensitive paths excluded |
| Live HTTP checks | `curl` against the running app: security headers, cookie flags, anonymous access to admin pages/APIs, `robots.txt` | Pass |
| Link & accessibility crawl | Custom crawler: every internal link/asset on `/`, `/projects`, project pages, `/admin/login` | 15 URLs, 0 broken; 0 missing `alt`, 0 unlabeled buttons, 1 `<h1>` per page, no duplicate ids |
| Automated tests | `pytest` (46 tests) | 46 passed |
| Manual code review | Auth, sessions, authorization, CSRF, input validation, output encoding, uploads, external calls, error handling, configuration | See §3 |

---

## 3. Security controls verified

### Authentication & sessions
- [x] Passwords hashed with **scrypt** (`werkzeug.security`); no plaintext storage.
- [x] **No hardcoded credentials.** The first admin is created from environment variables or `flask create-admin`.
- [x] Password policy: ≥ 12 characters, upper- and lower-case letters and a number (CLI and Security page).
- [x] **Login rate limit:** 5/minute, 20/hour per IP (`Flask-Limiter`). Over-limit attempts return HTTP 429.
- [x] Constant-time-ish failed logins: a dummy hash is checked when the username does not exist (no user enumeration by timing).
- [x] **Session fixation protection:** the session is cleared on login.
- [x] **Session revocation:** `session_version` is checked on every request; password change and "Sign out everywhere" invalidate all other sessions.
- [x] Cookies: `HttpOnly`, `SameSite=Lax`, `Secure` automatically in production (`APP_ENV=production`), 8-hour lifetime.
- [x] Logout is POST + CSRF-protected.
- [x] Open-redirect protection on `?next=` (only `/admin…` paths accepted). A test covers this.
- [x] Show/hide password toggle re-hides the password before submit; Caps Lock warning.

### Authorization
- [x] **Every `/admin` route** is protected server-side by a blueprint-level `before_request` + `login_required` (24 admin routes, 20 of them POST).
- [x] Anonymous requests: pages redirect to login (302); JSON APIs are rejected (400 CSRF / 401).
- [x] Draft design preview (`?preview=draft`) works only for signed-in admins.
- [x] Unpublished projects return 404 to the public.
- [x] Mass-assignment safe: admin forms only write fields declared in the resource registry; toggles only accept `visible` / `featured`.

### CSRF
- [x] Global `CSRFProtect` on every POST: HTML forms (hidden token) and fetch/JSON calls (`X-CSRFToken` header).

### Input validation
- [x] Server-side validation of every admin and contact field: required, max length, URL scheme (`http/https`, `mailto:` only for social links; `javascript:` rejected), email, `YYYY[-MM]` dates, number ranges, select whitelists, icon whitelist/regex.
- [x] Design Center values are validated against whitelists/regex/ranges **before** being written into CSS (prevents CSS/HTML injection through colours or fonts).
- [x] Site Content: known keys only, length limits, icon validation; unknown keys are dropped.
- [x] Contact form: validation, honeypot field, rate limit 5/hour and 20/day per IP; email header injection stripped (CR/LF) in notification mails.
- [x] Database access only through the SQLAlchemy ORM (parameterised); the one raw DDL statement (`ALTER TABLE` schema upgrade) uses constants only.

### Output encoding (XSS)
- [x] Jinja autoescaping on all templates. `|safe` is used only for server-generated, validated CSS variables.
- [x] `*highlight*` filter escapes text **before** adding `<mark>`. A test injects `<script>` and verifies it is escaped.
- [x] JSON in HTML only via `|tojson`.
- [x] All `Markup()` calls reviewed (bandit B704): they embed only escaped text, values from a fixed icon dictionary, or slugs matching `^[a-z0-9]{1,40}$`.

### File uploads
- [x] Images verified and **re-encoded to WebP** with Pillow, which strips EXIF/metadata and any embedded payload. SVG rejected; 40-megapixel decompression-bomb guard; 6 MB per image.
- [x] CV must start with the `%PDF-` magic bytes; 8 MB limit; total request limit 10 MB.
- [x] Random filenames (`secrets.token_hex`); user filenames never touch disk.
- [x] Deletions are confined to `static/uploads/` (path traversal blocked).

### HTTP security headers (verified live)
- [x] `Content-Security-Policy` with a **per-request script nonce**; no inline event handlers; `object-src 'none'`; `base-uri 'self'`; `form-action 'self'`; `frame-ancestors 'self'`.
- [x] `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` (camera/mic/geolocation off), `Cross-Origin-Opener-Policy: same-origin`.
- [x] `Strict-Transport-Security` in production.
- [x] Admin pages: `Cache-Control: no-store`, `X-Robots-Tag: noindex, nofollow`. `robots.txt` disallows `/admin`.

### Secrets & external services
- [x] `SECRET_KEY` from the environment; **the app refuses to start in production without it**. Development uses a random per-process key.
- [x] GitHub token (optional) used only server-side, never sent to the browser. Username validated by regex; requests time out; results cached; failures degrade gracefully.
- [x] No user-supplied URL is ever fetched by the server (no SSRF surface).

### Privacy
- [x] Private CV details (phone, home/permanent address, parents' names, date of birth, religion, marital status, height) are **not published**. A test enforces this.
- [x] No analytics or third-party trackers. The only third-party requests are Google Fonts, Simple Icons (brand logos) and GitHub avatars.

---

## 4. Findings

| ID | Severity | Finding | Status |
|---|---|---|---|
| **F1** | **Medium** | `tests/test_portfolio.py` contained the owner's **phone number and parents' names** in plain text (used to assert they were not published). Committing it would have published them on GitHub. | **Fixed:** the test now detects phone numbers by pattern and private words by SHA-256 hash, so the file no longer contains them. Verified that leak detection still works. |
| **F2** | Medium (bug) | Text saved from admin forms used Windows line endings (`\r\n`), so paragraph splitting failed. The whole About text rendered as one oversized block. | **Fixed:** paragraph splitting handles any line ending, all admin saves normalise line endings, and a regression test was added. |
| **F3** | Low | `Procfile` started **2 gunicorn workers** while rate-limit counters are stored in memory per process, which effectively doubled the login-attempt limit. | **Fixed:** `--workers 1 --threads 8`. For multiple workers or servers, set `RATELIMIT_STORAGE_URI` to Redis. |
| **F4** | Low | `pip 26.1.2` in the local `.venv` has a published advisory (PYSEC-2026-3721). It is a dev tool, not part of the app. | **Fixed:** upgraded pip in `.venv`. |
| F5 | Low | `.env` still contains `ADMIN_PASSWORD`. It is not committed (`.env` is git-ignored) but it is a plaintext password on disk. | **Owner action:** remove the line after changing your password in Admin → Security. |
| F6 | Info | A server process started earlier on port 5055 is running pre-audit code. | **Owner action:** restart it. |
| F7 | Info | CSP allows `'unsafe-inline'` for **styles** (not scripts). Needed for theme CSS variables and per-element style attributes. Script injection remains blocked by the nonce policy. | Accepted |
| F8 | Info | bandit: 6× B704 (`Markup`) and 1× B106 (dummy password hash used for timing-safe login). | Reviewed: false positives (see §3, Output encoding / Authentication). |
| F9 | Info | Rate-limit counters are in memory and reset on restart. | Accepted for a single small server; use Redis when scaling. |
| F10 | Info | No two-factor authentication for the admin. | Recommendation (see §7) |
| F11 | Info | The uploaded CV is publicly downloadable. | Reminder: upload a version **without** private details (address, family names, date of birth, phone). |
| F12 | Info | Every visitor gets a session cookie (needed for the contact form's CSRF token). | Accepted: contains only the CSRF token, no tracking. |
| F13 | Info | `static/uploads/` (photos, hero portrait, CV, project images) and `instance/` (database) are intentionally not in git. | Back them up separately; on a new server, restore them or re-upload via the admin. |

---

## 5. GitHub upload readiness certificate

**Status: ✅ Ready to publish**

| Check | Result |
|---|---|
| Files that would be committed | **70**: source code, templates, CSS/JS, tests, `README.md`, `Audit.md`, `requirements*.txt`, `Procfile`, `.env.example`, `.gitignore`, `.claude/skills/*` |
| Excluded by `.gitignore` | `.env` (secret key, admin password), `instance/` (database with password hashes and messages, plus backup DB), `static/uploads/` (personal media), `.venv/`, `venv/` (old broken env), `__pycache__/`, `.pytest_cache/`, `.claude/*` except skills |
| Real `SECRET_KEY` or admin password in committed files | **None found** |
| API tokens / private keys (GitHub, AWS, OpenAI, Slack, PEM) | **None found** |
| Private personal data (phone, addresses, family names, DOB) | **None found** (after fix F1) |
| Email addresses in committed files | Only the public contact email `sanjid.molik123@gmail.com` (already shown on the site) and `example.com` placeholders |
| Largest file | `static/css/site.css`, 111 KB. No binaries or large files. |
| `.env.example` | Contains no real values; documents every setting |

### How to upload

The project folder is not a git repository yet. Your existing repository `github.com/sanjidmolik/my_portfolio` contains the **old** version, so push the new one to a branch first and review it there:

```bash
cd E:/project/my_portfolio/my_portfolio-master
git init
git add .
git status            # double-check: .env, instance/ and static/uploads/ must NOT appear
git commit -m "Redesign: animated portfolio with secure admin CMS"
git branch -M redesign
git remote add origin https://github.com/sanjidmolik/my_portfolio.git
git push -u origin redesign
```

Then open a pull request from `redesign` into `main` on GitHub. Alternatively, create a new repository and push `main` there.

---

## 6. System audit (non-security)

| Area | Status | Notes |
|---|---|---|
| Automated tests | ✅ 46 passing | Auth, authorization, CSRF, rate limits, CRUD, uploads, design draft/publish, themes, Site Content, contact form, XSS escaping, GitHub fallbacks, private-data leak check, line-ending regression |
| Broken links | ✅ 0 / 15 internal URLs | Home, projects archive, every project page, login |
| Accessibility (automated) | ✅ 0 errors | Alt text, button labels, single `<h1>`, unique ids. Plus keyboard focus styles, skip link, `prefers-reduced-motion` and a visitor animation toggle. |
| Responsive | ✅ Verified 375 px / 1280–1600 px | No horizontal overflow on mobile |
| Browser console | ✅ No errors | |
| SEO | ✅ | Per-page titles/descriptions, Open Graph image, JSON-LD Person, `sitemap.xml`, `robots.txt`, canonical URLs (set `SITE_URL` in production) |
| Performance | ⚠️ Good, can improve | No JS framework or build step; images re-encoded to WebP and lazy-loaded; GitHub data cached. CSS is unminified (111 KB); enable gzip/brotli on the host or add a minify step. |
| Database | ✅ | SQLite (dev) / PostgreSQL (prod); automatic, data-safe column upgrades on startup |
| Admin UX | ✅ | Requirement hints, character counters, inline validation, unsaved-change warnings, live design preview, 7 one-click themes |

---

## 7. Production deployment checklist

- [ ] `APP_ENV=production` (enables `Secure` cookies, HSTS, strict CSRF referrer checks)
- [ ] Strong `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] `DATABASE_URL` pointing to PostgreSQL (or a persistent disk for SQLite)
- [ ] `SITE_URL=https://your-domain` (canonical links, sitemap, Open Graph)
- [ ] `TRUST_PROXY=1` when behind Render/Nginx/Cloudflare, so client IPs and HTTPS are detected correctly (rate limits depend on this)
- [ ] Persistent storage for `static/uploads/`
- [ ] HTTPS only
- [ ] Create the admin with `flask --app app create-admin`, then **do not** keep `ADMIN_PASSWORD` in the environment
- [ ] Optional: `GITHUB_TOKEN` (no scopes needed), SMTP settings for contact-form email alerts, Redis for `RATELIMIT_STORAGE_URI`

## 8. Recommendations (next steps)

1. **Two-factor authentication** (TOTP) for the admin account.
2. **Audit log** of admin changes (who changed what, when), beyond the login events already logged.
3. **Dependabot** (or a monthly `pip-audit`) on the GitHub repository to catch new vulnerabilities.
4. Hash-pinned requirements (`pip-compile --generate-hashes`).
5. CSS minification and response compression for faster mobile loads.
6. A `/.well-known/security.txt` with a contact address for vulnerability reports.
7. A retention policy for contact messages (e.g. delete after 12 months).
8. Delete the old broken `venv/` folder and, once you are happy, the `_legacy_backup/` folder next to the project.

---

*Re-run this audit:* `pytest` · `bandit -r portfolio app.py` · `pip-audit -r requirements.txt` · and check `git status` before every push.
