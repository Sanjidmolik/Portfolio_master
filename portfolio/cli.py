"""Management commands: `flask --app app <command>`."""
from __future__ import annotations

import os

import click

from .extensions import db
from .models import AdminUser

MIN_PASSWORD = 12


def validate_password(pw: str) -> str | None:
    if len(pw) < MIN_PASSWORD:
        return f"Password must be at least {MIN_PASSWORD} characters."
    if pw.lower() == pw or pw.upper() == pw or not any(c.isdigit() for c in pw):
        return "Use upper- and lower-case letters and at least one number."
    return None


def bootstrap_admin_from_env(app) -> None:
    """Create the first admin from ADMIN_USERNAME / ADMIN_PASSWORD if none exists."""
    username = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not username or not password or AdminUser.query.count():
        return
    err = validate_password(password)
    if err:
        app.logger.error("ADMIN_PASSWORD rejected: %s", err)
        return
    user = AdminUser(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    app.logger.warning("Created initial admin '%s' from environment. "
                       "Remove ADMIN_PASSWORD from the environment now.", username)


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create tables and seed initial content (safe to re-run)."""
        from .seed import seed_if_empty
        db.create_all()
        click.echo("Seeded initial content." if seed_if_empty() else "Database already initialised.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.password_option(confirmation_prompt=True)
    def create_admin(username, password):
        """Create an administrator account."""
        username = username.strip()
        if AdminUser.query.filter_by(username=username).first():
            raise click.ClickException("That username already exists.")
        err = validate_password(password)
        if err:
            raise click.ClickException(err)
        user = AdminUser(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin '{username}' created. Sign in at /admin.")

    @app.cli.command("reset-admin-password")
    @click.option("--username", prompt=True)
    @click.password_option(confirmation_prompt=True)
    def reset_password(username, password):
        """Reset a password and sign out all of that admin's sessions."""
        user = AdminUser.query.filter_by(username=username.strip()).first()
        if not user:
            raise click.ClickException("No such admin.")
        err = validate_password(password)
        if err:
            raise click.ClickException(err)
        user.set_password(password)
        user.session_version += 1
        db.session.commit()
        click.echo("Password updated; existing sessions were revoked.")

    @app.cli.command("sync-cv")
    def sync_cv():
        """Apply the CV content in portfolio/cv_content.py (safe to re-run)."""
        from .cv_content import sync_cv_content
        for line in sync_cv_content():
            click.echo(f"  {line}")

    @app.cli.command("github-refresh")
    def github_refresh():
        """Refresh the cached GitHub data now."""
        from .github import get_github_data
        from .models import Profile
        data = get_github_data(Profile.get().github_username, force=True)
        click.echo("Refreshed." if data else "No GitHub username set or fetch failed.")
