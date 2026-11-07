"""Portfolio application factory."""
from __future__ import annotations

import os
import re
import secrets

from markupsafe import Markup, escape

from flask import Flask, g, render_template, request
from flask_wtf.csrf import CSRFError

from .config import BASE_DIR, Config, ensure_secret_key
from .extensions import csrf, db, limiter


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
        instance_path=str(BASE_DIR / "instance"),
    )
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    ensure_secret_key(app)

    if app.config.get("TRUST_PROXY") or os.environ.get("TRUST_PROXY", "").lower() in ("1", "true", "yes"):
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from . import admin, auth, public
    app.register_blueprint(public.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)

    from .cli import register_cli
    register_cli(app)

    from .icons import any_icon, icon_svg, skill_icon
    app.jinja_env.globals.update(icon=icon_svg, skill_icon=skill_icon, any_icon=any_icon)

    app.jinja_env.filters["highlight"] = highlight

    _register_security(app)
    _register_errors(app)

    with app.app_context():
        db.create_all()
        _upgrade_schema()
        if not app.config.get("SKIP_SEED"):
            from .seed import seed_if_empty
            seed_if_empty()
        from .cli import bootstrap_admin_from_env
        bootstrap_admin_from_env(app)

    return app


# Columns added after the first release. create_all() never alters existing tables,
# so add them in place (works on SQLite and PostgreSQL).
_ADDED_COLUMNS = [("profile", "hero_image", "VARCHAR(255) DEFAULT ''")]


def _upgrade_schema() -> None:
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)
    for table, column, ddl in _ADDED_COLUMNS:
        if table in insp.get_table_names() and column not in {c["name"] for c in insp.get_columns(table)}:
            db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            db.session.commit()


_HIGHLIGHT_RE = re.compile(r"\*([^*\n]{1,80})\*")


def highlight(text) -> Markup:
    """Escape text, then turn *phrase* into <mark>phrase</mark> (admin-editable emphasis)."""
    return Markup(_HIGHLIGHT_RE.sub(r"<mark>\1</mark>", str(escape(text or ""))))


def _register_security(app: Flask) -> None:
    @app.before_request
    def _nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.after_request
    def _headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        resp.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if app.config.get("IS_PRODUCTION"):
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        nonce = getattr(g, "csp_nonce", "")
        resp.headers.setdefault("Content-Security-Policy", "; ".join([
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}'",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com data:",
            "img-src 'self' data: https://avatars.githubusercontent.com https://cdn.simpleicons.org",
            "connect-src 'self'",
            "frame-src 'self'",
            "frame-ancestors 'self'",
            "form-action 'self'",
            "base-uri 'self'",
            "object-src 'none'",
        ]))
        if request.path.startswith("/admin"):
            resp.headers["Cache-Control"] = "no-store"
            resp.headers["X-Robots-Tag"] = "noindex, nofollow"
        return resp


def _register_errors(app: Flask) -> None:
    def wants_json():
        return request.is_json or request.accept_mimetypes.best == "application/json"

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        if wants_json():
            return {"ok": False, "error": "Your session expired. Refresh the page and try again."}, 400
        return render_template("error.html", code=400,
                               title="Session expired",
                               message="Your form session expired. Go back, refresh and try again."), 400

    @app.errorhandler(429)
    def ratelimited(e):
        msg = "Too many requests. Please slow down and try again later."
        if wants_json():
            return {"ok": False, "error": msg}, 429
        if request.path.startswith("/admin/login"):
            from flask import flash
            flash("Too many login attempts. Please wait a few minutes and try again.", "error")
            return render_template("admin/login.html", has_admin=True), 429
        return render_template("error.html", code=429, title="Slow down", message=msg), 429

    for code, title, message in [
        (401, "Unauthorized", "You need to sign in to do that."),
        (403, "Forbidden", "You don't have access to this page."),
        (404, "Signal lost", "The page you're looking for isn't on this channel."),
        (413, "File too large", "That upload is bigger than the allowed size."),
        (500, "Transmission error", "Something went wrong on our side. Please try again."),
    ]:
        def handler(e, code=code, title=title, message=message):
            if wants_json():
                return {"ok": False, "error": message}, code
            return render_template("error.html", code=code, title=title, message=message), code
        app.register_error_handler(code, handler)
