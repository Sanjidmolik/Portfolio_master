"""Application configuration, read from environment variables.

Nothing secret is hardcoded here: SECRET_KEY, admin credentials, database URL,
GitHub token and SMTP credentials all come from the environment (.env in dev).
"""
import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        instance = BASE_DIR / "instance"
        instance.mkdir(exist_ok=True)
        return f"sqlite:///{instance / 'portfolio.db'}"
    # Heroku/Render style URLs use postgres:// which SQLAlchemy 2 rejects.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Config:
    ENV_NAME = os.environ.get("FLASK_ENV", os.environ.get("APP_ENV", "development"))
    IS_PRODUCTION = ENV_NAME == "production"

    SECRET_KEY = os.environ.get("SECRET_KEY") or ""

    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessions / cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", IS_PRODUCTION)
    SESSION_COOKIE_NAME = "portfolio_session"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.environ.get("ADMIN_SESSION_HOURS", "8")))

    # CSRF
    WTF_CSRF_TIME_LIMIT = None  # token lives as long as the session
    WTF_CSRF_SSL_STRICT = IS_PRODUCTION

    # Uploads
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    MAX_IMAGE_BYTES = 6 * 1024 * 1024
    MAX_DOCUMENT_BYTES = 8 * 1024 * 1024

    # Rate limiting
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    LOGIN_RATE_LIMIT = os.environ.get("LOGIN_RATE_LIMIT", "5 per minute;20 per hour")
    CONTACT_RATE_LIMIT = os.environ.get("CONTACT_RATE_LIMIT", "5 per hour;20 per day")

    # GitHub (server-side only, never sent to the browser)
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
    GITHUB_CACHE_SECONDS = int(os.environ.get("GITHUB_CACHE_SECONDS", "3600"))

    # Optional SMTP notifications for contact messages
    SMTP_HOST = os.environ.get("SMTP_HOST", "").strip()
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "").strip()
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = _bool("SMTP_USE_TLS", True)
    CONTACT_NOTIFY_EMAIL = os.environ.get("CONTACT_NOTIFY_EMAIL", "").strip()

    SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")


def ensure_secret_key(app) -> None:
    """Refuse to run in production without a real SECRET_KEY.

    In development a random per-process key is generated (sessions reset on
    restart), so nobody is tempted to commit a hardcoded one.
    """
    if app.config.get("SECRET_KEY"):
        return
    if app.config.get("IS_PRODUCTION") and not app.config.get("TESTING"):
        raise RuntimeError("SECRET_KEY must be set in production (see .env.example).")
    app.config["SECRET_KEY"] = secrets.token_hex(32)
    app.logger.warning("SECRET_KEY not set - using a temporary random key (development only).")
