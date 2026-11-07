"""Admin authentication: login, logout, session validation, route protection."""
from __future__ import annotations

import secrets
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template,
                   request, session, url_for)

from .extensions import db, limiter
from .models import AdminUser, utcnow

bp = Blueprint("auth", __name__, url_prefix="/admin")

# A dummy hash so failed logins for unknown users take the same time.
_DUMMY = AdminUser(username="_", password_hash="")
_DUMMY.set_password(secrets.token_hex(16))


def current_admin() -> AdminUser | None:
    if "admin_user" in g:
        return g.admin_user
    user = None
    uid, ver = session.get("admin_id"), session.get("admin_ver")
    if uid is not None:
        user = db.session.get(AdminUser, uid)
        if user is None or user.session_version != ver:
            session.clear()
            user = None
    g.admin_user = user
    return user


def login_required(view):
    """Server-side authorization for every admin view and admin API."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_admin() is None:
            if request.accept_mimetypes.best == "application/json" or request.is_json:
                abort(401)
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def _safe_next(target: str | None) -> str:
    if target and target.startswith("/admin") and not target.startswith("//"):
        return target
    return url_for("admin.dashboard")


def _login_limit():
    return current_app.config["LOGIN_RATE_LIMIT"]


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit(_login_limit, methods=["POST"],
               error_message="Too many login attempts. Please wait and try again.")
def login():
    if current_admin():
        return redirect(url_for("admin.dashboard"))
    has_admin = AdminUser.query.count() > 0
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()[:64]
        password = request.form.get("password") or ""
        user = AdminUser.query.filter_by(username=username).first() if username else None
        ok = (user or _DUMMY).check_password(password) and user is not None
        if ok:
            session.clear()  # prevent session fixation
            session.permanent = True
            session["admin_id"] = user.id
            session["admin_ver"] = user.session_version
            user.last_login_at = utcnow()
            db.session.commit()
            current_app.logger.info("Admin login: %s from %s", username, request.remote_addr)
            return redirect(_safe_next(request.args.get("next")))
        current_app.logger.warning("Failed admin login for %r from %s", username, request.remote_addr)
        flash("Invalid username or password.", "error")
    return render_template("admin/login.html", has_admin=has_admin), (200 if request.method == "GET" else 401)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
