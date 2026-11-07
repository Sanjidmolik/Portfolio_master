---
name: security-review
description: Security review and hardening for the portfolio and its admin Control Center - authentication, session management, authorization of admin routes and APIs, CSRF, input validation, XSS/injection, file uploads, rate limiting, secrets, security headers/CSP and dependency risk. Use when touching auth, admin routes, forms, uploads, external integrations, templates that render user content, configuration or deployment, before releasing, or when asked to audit or "check security".
---

# Security Review

Think like an attacker, report like an engineer. Every finding needs a concrete exploit
scenario, a severity, and a minimal fix. Do not report theoretical issues without a path.

## 1. Scope and context

Read `portfolio/auth.py`, `portfolio/admin.py`, `portfolio/__init__.py` (headers/CSP/errors),
`portfolio/config.py`, `portfolio/uploads.py`, `portfolio/public.py` (contact form),
`portfolio/design.py` (values injected into CSS), templates that render user content, and
`static/js/*.js`. For a diff review, start from `git diff` (if a repo) or the changed files the
user names, then trace data flow into and out of them.

Existing controls to verify are still intact (regressions are the most common bug):
- `admin.bp.before_request` + `login_required` protect **every** `/admin` route; JSON gets 401.
- Session: cleared on login (fixation), `session_version` checked on every request (revocation),
  `HttpOnly`, `SameSite=Lax`, `Secure` in production, 8h lifetime.
- scrypt password hashing; dummy hash for unknown users; password policy in `cli.validate_password`.
- Global `CSRFProtect`; fetch calls send `X-CSRFToken`.
- Flask-Limiter on login and contact; `_safe_next()` prevents open redirects.
- CSP with per-request nonce (no inline handlers / `onclick=` allowed), `X-Frame-Options:
  SAMEORIGIN`, `nosniff`, HSTS in production, `no-store` + `noindex` on admin.
- Uploads re-encoded via Pillow to WebP, SVG rejected, PDF magic bytes, random names, size caps.
- Design JSON passes `design.sanitize()` (hex regex, whitelists, numeric ranges) before CSS output.
- URL fields restricted to `http(s)://` (and `mailto:` for socials only).

## 2. Checklist by category (OWASP-aligned)

**AuthN/session**: no hardcoded or default credentials; secrets from env; production refuses to
boot without `SECRET_KEY`; login responses don't reveal which field was wrong; logout is POST.

**AuthZ**: new admin endpoints are inside the `admin` blueprint (or explicitly decorated);
object lookups can't reach unpublished content publicly (`visible` checks, e.g. `project_detail`);
preview mode (`?preview=draft`) requires `current_admin()`.

**Input/output**: all writes validated server-side (length, type, whitelist); Jinja autoescaping
never bypassed - flag every `|safe`, `Markup()`, `innerHTML` with non-constant data; JSON in HTML
only via `|tojson`; email headers stripped of CR/LF; no string-built SQL (ORM/bound params only).

**Files**: extension *and* content validation; re-encode images; no user-controlled paths
(`delete_upload` confines to `uploads/`); `MAX_CONTENT_LENGTH` enforced; no execution from upload dir.

**Browser**: CSP not weakened (`unsafe-inline` scripts, wildcard sources); external links use
`rel="noopener noreferrer"`; `postMessage` handlers check `origin` and `source`.

**Abuse**: rate limits on any endpoint that sends email, writes to DB anonymously, or
authenticates; honeypot on public forms; limiter storage shared (Redis) when multi-worker;
`TRUST_PROXY` set behind a proxy so IP-based limits work.

**Secrets & config**: `.env` gitignored; `.env.example` has no real values; tokens (GitHub, SMTP)
used server-side only and never logged; debug mode off in production.

**Dependencies**: versions pinned; check for known CVEs (`pip-audit` if available - ask before
installing); remove unused packages.

## 3. Severity

- **Critical** - unauthenticated admin access, RCE, auth bypass, secret exposure.
- **High** - stored XSS, CSRF on state-changing admin action, IDOR exposing hidden content,
  unrestricted upload.
- **Medium** - missing rate limit, weak session settings, open redirect, info leak in errors.
- **Low** - hardening/headers/defense-in-depth.

## 4. Workflow

1. Define scope (whole app / diff / feature) and list entry points (routes, forms, APIs, uploads).
2. Trace untrusted input from each entry point to sinks (DB, template, CSS, filesystem, email,
   external API, redirect).
3. Verify each control in section 1 still holds; test with the Flask test client - e.g.
   anonymous POST to an admin endpoint, missing CSRF token, malicious upload, `javascript:` URL,
   `<script>` in a text field, `next=https://evil`.
4. Report findings ranked by severity: location (`file:line`), scenario, impact, fix.
5. When fixing: smallest change, add a regression test to `tests/test_portfolio.py` for each
   fixed issue, run the full suite.

## 5. Report format

```
[SEVERITY] Title
Location: portfolio/admin.py:123
Scenario: <who> can <do what> by <how>
Impact: <what is exposed / changed>
Fix: <minimal change>  Test: <test name added>
```
End with "Controls verified" listing what was checked and passed, and anything not checked.

## 6. Quality checklist

- [ ] Every `/admin` route and admin API requires auth server-side (test with anonymous client)
- [ ] Every POST is CSRF-protected
- [ ] No `|safe` / `innerHTML` with untrusted data; CSP unchanged or stricter
- [ ] Uploads validated by content and re-encoded
- [ ] Rate limits on login, contact and any new anonymous write
- [ ] No secrets in code, templates, JS, logs or git
- [ ] Regression tests added for every fix; `pytest` green
