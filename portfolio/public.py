"""Public portfolio routes."""
from __future__ import annotations

import io
import re
import smtplib
from email.message import EmailMessage

from flask import (Blueprint, Response, abort, current_app, flash, g, redirect,
                   render_template, request, send_file, url_for)

from . import design as design_mod
from .auth import current_admin
from .extensions import db, limiter
from .github import get_github_data
from .icons import icon_svg, skill_icon
from .site_content import get_content
from .models import (Certification, Education, Experience, Message, Profile, Project,
                     Skill, SocialLink, TimelineEvent)

bp = Blueprint("public", __name__)

EMAIL_RE = re.compile(r"^[^@\s<>\"']{1,64}@[^@\s<>\"']{1,190}\.[A-Za-z]{2,24}$")


def active_design() -> dict:
    """Published design, or the draft when an admin is previewing."""
    if "design" not in g:
        if request.args.get("preview") == "draft" and current_admin():
            g.design, g.preview = design_mod.get_draft(), True
        else:
            g.design, g.preview = design_mod.get_published(), False
    return g.design


@bp.app_context_processor
def inject_globals():
    d = active_design()
    prof = Profile.get()
    # Sections with no published content are hidden (and left out of the nav).
    available = {
        "hero": True,
        "about": bool(prof.about or TimelineEvent.published().count()),
        "experience": Experience.published().count() > 0,
        "skills": Skill.published().count() > 0,
        "projects": Project.published().count() > 0,
        "education": Education.published().count() + Certification.published().count() > 0,
        "github": bool(prof.github_username),
        "contact": True,
    }
    sections = [s for s in d["sections"] if available.get(s["key"])]
    preview = g.get("preview", False)
    return {
        "content": get_content(),
        "profile": prof,
        "available": available,
        "page_sections": sections if preview else [s for s in sections if s["enabled"]],
        "socials": SocialLink.published().all(),
        "design": d,
        "is_preview": g.get("preview", False),
        "design_css": design_mod.css_variables(d),
        "font_url": design_mod.font_url(d),
        "body_classes": design_mod.body_classes(d),
        "nav_sections": [s for s in sections if s["key"] != "hero" and (s["enabled"] or preview)],
        "icon": icon_svg,
        "skill_icon": skill_icon,
        "csp_nonce": getattr(g, "csp_nonce", ""),
        "now_year": __import__("datetime").date.today().year,
        "site_url": current_app.config.get("SITE_URL") or request.url_root.rstrip("/"),
    }


def access_pass() -> dict:
    """Facts for the MCR access-pass card, derived from published content only."""
    xps = Experience.published().all()
    current = next((x for x in xps if x.is_current), xps[0] if xps else None)
    starts = [x.start_date[:4] for x in xps if x.start_date]
    study = next((e for e in Education.published().all() if e.is_current), None)
    return {
        "role": current.position if current else "",
        "station": current.company if current else "",
        "since": min(starts) if starts else "",
        "study": study.institution if study else "",
        "degree": study.degree if study else "",
        "current_since": current.start_date[:4] if current and current.start_date else "",
        "on_duty": bool(current and current.is_current),
    }


def skill_channels(limit: int = 3, per: int = 3) -> list[dict]:
    """Top skill categories with their first few skills (for the dashboard)."""
    out: dict[str, list[str]] = {}
    for s in Skill.published().all():
        out.setdefault(s.category, [])
        if len(out[s.category]) < per:
            out[s.category].append(s.name)
    return [{"name": k, "skills": v} for k, v in list(out.items())[:limit]]


def _home_context():
    skills = Skill.published().all()
    categories = []
    for s in skills:
        if s.category not in categories:
            categories.append(s.category)
    profile = Profile.get()
    return {
        "timeline": TimelineEvent.published().all(),
        "experiences": Experience.published().all(),
        "skills": skills,
        "skill_categories": categories,
        "projects": Project.published().filter_by(featured=True).all() or Project.published().limit(6).all(),
        "project_total": Project.published().count(),
        "education": Education.published().all(),
        "certifications": Certification.published().filter(Certification.kind != "award").all(),
        "awards": Certification.published().filter_by(kind="award").all(),
        "has_github": bool(profile.github_username),
        "access": access_pass(),
    }


@bp.route("/")
def home():
    return render_template("public/home.html", **_home_context())


@bp.route("/about")
def about():
    return redirect(url_for("public.home", _anchor="about"), code=301)


@bp.route("/projects")
def projects():
    items = Project.published().all()
    techs = sorted({t for p in items for t in p.tech_list}, key=str.lower)
    return render_template("public/projects.html", items=items, techs=techs)


@bp.route("/projects/<slug>")
def project_detail(slug):
    project = Project.query.filter_by(slug=slug).first()
    if project is None or (not project.visible and not current_admin()):
        abort(404)
    others = Project.published().filter(Project.id != project.id).limit(3).all()
    return render_template("public/project_detail.html", project=project, others=others)


@bp.route("/resume")
def resume():
    prof = Profile.get()
    if not prof.resume:
        abort(404)
    return redirect(url_for("static", filename=prof.resume))


@bp.route("/fragments/github")
def github_fragment():
    prof = Profile.get()
    data = get_github_data(prof.github_username)
    resp = current_app.make_response(render_template("public/_github.html", gh=data,
                                                     username=prof.github_username,
                                                     channels=skill_channels()))
    resp.headers["Cache-Control"] = "public, max-age=300"
    return resp


# ---------------------------------------------------------------- contact
def _validate_contact(form) -> tuple[dict, dict]:
    data = {
        "name": (form.get("name") or "").strip(),
        "email": (form.get("email") or "").strip(),
        "subject": (form.get("subject") or "").strip(),
        "message": (form.get("message") or "").strip(),
    }
    errors = {}
    if not 2 <= len(data["name"]) <= 120:
        errors["name"] = "Please enter your name (2-120 characters)."
    if not EMAIL_RE.match(data["email"]) or len(data["email"]) > 200:
        errors["email"] = "Please enter a valid email address."
    if len(data["subject"]) > 200:
        errors["subject"] = "Subject is too long (max 200 characters)."
    if not 10 <= len(data["message"]) <= 5000:
        errors["message"] = "Message should be between 10 and 5000 characters."
    return data, errors


def _notify(msg: Message) -> None:
    cfg = current_app.config
    if not (cfg["SMTP_HOST"] and cfg["CONTACT_NOTIFY_EMAIL"]):
        return
    clean = lambda s: re.sub(r"[\r\n]+", " ", s)[:200]  # no header injection
    em = EmailMessage()
    em["Subject"] = clean(f"Portfolio message: {msg.subject or msg.name}")
    em["From"] = cfg["SMTP_USER"] or cfg["CONTACT_NOTIFY_EMAIL"]
    em["To"] = cfg["CONTACT_NOTIFY_EMAIL"]
    em["Reply-To"] = clean(msg.email)
    em.set_content(f"From: {msg.name} <{msg.email}>\n\n{msg.body}")
    try:
        with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=10) as s:
            if cfg["SMTP_USE_TLS"]:
                s.starttls()
            if cfg["SMTP_USER"]:
                s.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            s.send_message(em)
    except Exception as exc:
        current_app.logger.warning("Contact notification email failed: %s", exc)


def _contact_limit():
    return current_app.config["CONTACT_RATE_LIMIT"]


@bp.route("/contact", methods=["GET", "POST"])
@limiter.limit(_contact_limit, methods=["POST"])
def contact():
    if request.method == "GET":
        return redirect(url_for("public.home", _anchor="contact"), code=301)
    wants_json = request.accept_mimetypes.best == "application/json"
    # Honeypot: real visitors never fill the hidden "website" field.
    if request.form.get("website"):
        return ({"ok": True, "message": "Thanks! Your message has been sent."} if wants_json
                else redirect(url_for("public.home", _anchor="contact")))
    data, errors = _validate_contact(request.form)
    if errors:
        if wants_json:
            return {"ok": False, "error": "Please fix the highlighted fields.", "fields": errors}, 422
        for e in errors.values():
            flash(e, "error")
        return redirect(url_for("public.home", _anchor="contact"))
    msg = Message(name=data["name"], email=data["email"], subject=data["subject"], body=data["message"])
    db.session.add(msg)
    db.session.commit()
    _notify(msg)
    text = get_content()["contact_success"]
    if wants_json:
        return {"ok": True, "message": text}
    flash(text, "success")
    return redirect(url_for("public.home", _anchor="contact"))


# ---------------------------------------------------------------- SEO
@bp.route("/robots.txt")
def robots():
    base = current_app.config.get("SITE_URL") or request.url_root.rstrip("/")
    body = f"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /fragments/\n\nSitemap: {base}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap():
    base = current_app.config.get("SITE_URL") or request.url_root.rstrip("/")
    urls = [(f"{base}/", None), (f"{base}/projects", None)]
    for p in Project.published().all():
        urls.append((f"{base}/projects/{p.slug}", p.updated_at.date().isoformat()))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in urls:
        xml.append(f"<url><loc>{loc}</loc>" + (f"<lastmod>{mod}</lastmod>" if mod else "") + "</url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")


@bp.route("/og-image.png")
def og_image():
    from .og import render_og
    prof = Profile.get()
    d = design_mod.get_published()
    png = render_og(prof.full_name, prof.headline, d["colors"])
    resp = send_file(io.BytesIO(png), mimetype="image/png", max_age=3600)
    return resp


@bp.route("/healthz")
def healthz():
    db.session.execute(db.text("SELECT 1"))
    return {"ok": True}
