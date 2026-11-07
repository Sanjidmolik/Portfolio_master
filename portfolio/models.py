"""Database models. Works on SQLite (dev) and PostgreSQL (production)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from sqlalchemy import JSON
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


_PARA_RE = re.compile(r"\n[ \t]*\n")


def split_paragraphs(text: str | None) -> list[str]:
    """Split on blank lines, whatever the line endings (browsers submit \\r\\n)."""
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    return [p.strip() for p in _PARA_RE.split(text) if p.strip()]


def split_lines(text: str | None) -> list[str]:
    return [ln.strip(" \t-•*") for ln in (text or "").splitlines() if ln.strip(" \t-•*")]


def split_tags(text: str | None) -> list[str]:
    return [t.strip() for t in (text or "").split(",") if t.strip()]


class OrderedMixin:
    sort_order = db.Column(db.Integer, nullable=False, default=0, index=True)
    visible = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    @classmethod
    def published(cls):
        return cls.query.filter_by(visible=True).order_by(cls.sort_order, cls.id)

    @classmethod
    def ordered(cls):
        return cls.query.order_by(cls.sort_order, cls.id)


class AdminUser(db.Model):
    __tablename__ = "admin_users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Bumped on password change / "log out everywhere" to invalidate sessions.
    session_version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    """Singleton row holding identity + contact info."""
    __tablename__ = "profile"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False, default="")
    short_name = db.Column(db.String(40), default="")
    headline = db.Column(db.String(160), default="")
    rotating_titles = db.Column(db.Text, default="")  # one per line
    short_intro = db.Column(db.Text, default="")
    about = db.Column(db.Text, default="")
    career_goals = db.Column(db.Text, default="")
    avatar = db.Column(db.String(255), default="")
    hero_image = db.Column(db.String(255), default="")  # large portrait for the hero (transparent PNG works best)
    resume = db.Column(db.String(255), default="")
    email = db.Column(db.String(160), default="")
    phone = db.Column(db.String(60), default="")
    location = db.Column(db.String(120), default="")
    availability = db.Column(db.String(160), default="")
    github_username = db.Column(db.String(60), default="")
    seo_title = db.Column(db.String(160), default="")
    seo_description = db.Column(db.String(300), default="")
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    @property
    def titles(self) -> list[str]:
        return split_lines(self.rotating_titles)

    @property
    def about_paragraphs(self) -> list[str]:
        return split_paragraphs(self.about)

    @property
    def about_parts(self) -> tuple[str, list[str]]:
        """(opening line, body paragraphs). A long first paragraph only lends its first sentence."""
        paras = self.about_paragraphs
        if not paras:
            return "", []
        first, rest = paras[0], paras[1:]
        if len(first) <= 200:
            return first, rest
        m = re.match(r"(.{20,200}?[.!?])\s+(.+)", first, re.S)
        if m:
            return m.group(1), [m.group(2)] + rest
        return "", paras

    @property
    def initials(self) -> str:
        parts = [p for p in (self.full_name or "").split() if p]
        return "".join(p[0] for p in parts[:2]).upper() or "SR"

    @classmethod
    def get(cls) -> "Profile":
        prof = cls.query.first()
        if prof is None:
            prof = cls(full_name="")
            db.session.add(prof)
            db.session.commit()
        return prof


class SocialLink(OrderedMixin, db.Model):
    __tablename__ = "social_links"
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(40), nullable=False)  # github, linkedin, email, x, ...
    label = db.Column(db.String(80), default="")
    url = db.Column(db.String(500), nullable=False)
    handle = db.Column(db.String(120), default="")


class TimelineEvent(OrderedMixin, db.Model):
    """Career-journey milestones shown in the About section."""
    __tablename__ = "timeline_events"
    id = db.Column(db.Integer, primary_key=True)
    period = db.Column(db.String(60), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    kind = db.Column(db.String(30), default="milestone")  # broadcast, development, security, education, milestone
    description = db.Column(db.Text, default="")


class Experience(OrderedMixin, db.Model):
    __tablename__ = "experiences"
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(160), nullable=False)
    position = db.Column(db.String(160), nullable=False)
    location = db.Column(db.String(120), default="")
    employment_type = db.Column(db.String(60), default="")
    start_date = db.Column(db.String(20), default="")  # YYYY-MM
    end_date = db.Column(db.String(20), default="")
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, default="")
    responsibilities = db.Column(db.Text, default="")
    achievements = db.Column(db.Text, default="")
    technologies = db.Column(db.Text, default="")
    logo = db.Column(db.String(255), default="")
    company_url = db.Column(db.String(500), default="")

    @property
    def responsibility_list(self):
        return split_lines(self.responsibilities)

    @property
    def achievement_list(self):
        return split_lines(self.achievements)

    @property
    def tech_list(self):
        return split_tags(self.technologies)


class Skill(OrderedMixin, db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(60), nullable=False, default="Tools")
    icon = db.Column(db.String(80), default="")  # Simple Icons slug or built-in icon key
    icon_image = db.Column(db.String(255), default="")  # uploaded icon (overrides slug)
    description = db.Column(db.String(300), default="")
    proficiency = db.Column(db.String(30), default="")  # optional: Learning / Familiar / Proficient / Advanced
    years = db.Column(db.Float)


class Project(OrderedMixin, db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    tagline = db.Column(db.String(200), default="")
    summary = db.Column(db.Text, default="")
    description = db.Column(db.Text, default="")
    highlights = db.Column(db.Text, default="")
    thumbnail = db.Column(db.String(255), default="")
    tech_stack = db.Column(db.Text, default="")
    github_url = db.Column(db.String(500), default="")
    demo_url = db.Column(db.String(500), default="")
    status = db.Column(db.String(30), default="in-progress")
    featured = db.Column(db.Boolean, default=False)
    images = db.relationship(
        "ProjectImage", backref="project", cascade="all, delete-orphan",
        order_by="ProjectImage.sort_order",
    )

    STATUSES = [("planning", "Planning"), ("in-progress", "In progress"),
                ("completed", "Completed"), ("maintained", "Maintained"), ("archived", "Archived")]

    @property
    def tech_list(self):
        return split_tags(self.tech_stack)

    @property
    def highlight_list(self):
        return split_lines(self.highlights)

    @property
    def description_paragraphs(self):
        return split_paragraphs(self.description)

    @property
    def status_label(self):
        return dict(self.STATUSES).get(self.status, self.status.title())


class ProjectImage(db.Model):
    __tablename__ = "project_images"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(200), default="")
    sort_order = db.Column(db.Integer, default=0)


class Education(OrderedMixin, db.Model):
    __tablename__ = "education"
    id = db.Column(db.Integer, primary_key=True)
    institution = db.Column(db.String(200), nullable=False)
    degree = db.Column(db.String(200), nullable=False)
    field = db.Column(db.String(200), default="")
    start_date = db.Column(db.String(20), default="")
    end_date = db.Column(db.String(20), default="")
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, default="")
    logo = db.Column(db.String(255), default="")


class Certification(OrderedMixin, db.Model):
    __tablename__ = "certifications"
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), default="certification")  # certification | award | course
    name = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200), default="")
    date = db.Column(db.String(20), default="")
    credential_url = db.Column(db.String(500), default="")
    description = db.Column(db.Text, default="")


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), default="")
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


class Setting(db.Model):
    """Generic JSON key/value store (design draft/published, caches)."""
    __tablename__ = "settings"
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(JSON, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    @classmethod
    def read(cls, key: str, default=None):
        row = db.session.get(cls, key)
        if row is None:
            return default
        # Return a deep copy so callers can't mutate the tracked object.
        return json.loads(json.dumps(row.value))

    @classmethod
    def write(cls, key: str, value) -> None:
        row = db.session.get(cls, key)
        if row is None:
            db.session.add(cls(key=key, value=value))
        else:
            row.value = value
            row.updated_at = utcnow()
        db.session.commit()
