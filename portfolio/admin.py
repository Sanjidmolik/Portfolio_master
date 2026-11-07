"""Portfolio Control Center (admin panel).

Every route in this blueprint is protected server-side by ``login_required``
(applied in ``before_request``) and every POST is CSRF-protected globally.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from sqlalchemy import String

from . import design as design_mod
from .auth import current_admin, login_required
from .cli import validate_password
from .extensions import db
from .github import get_github_data
from .icons import BUILTIN_SKILL_ICONS
from .models import (Certification, Education, Experience, Message, Profile, Project,
                     ProjectImage, Skill, SocialLink, TimelineEvent)
from .uploads import UploadError, delete_upload, save_image, save_pdf

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
@login_required
def _require_login():
    return None


@bp.app_context_processor
def _admin_ctx():
    if not request.path.startswith("/admin"):
        return {}
    unread = 0
    if current_admin():
        unread = Message.query.filter_by(is_read=False).count()
    return {"admin_user": current_admin(), "unread_count": unread, "resources": RESOURCES}


# ------------------------------------------------------------------ fields
URL_RE = re.compile(r"^https?://[^\s<>\"']+$", re.I)
EMAIL_RE = re.compile(r"^[^@\s<>\"']+@[^@\s<>\"']+\.[A-Za-z]{2,}$")
MONTH_RE = re.compile(r"^\d{4}(-(0[1-9]|1[0-2]))?$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Field:
    name: str
    label: str
    type: str = "text"  # text textarea lines tags url email month number float select bool image icon slug datalist
    required: bool = False
    help: str = ""
    choices: list = field(default_factory=list)
    placeholder: str = ""
    wide: bool = False
    upload_dir: str = "images"
    max_dim: int = 1600


@dataclass
class Resource:
    key: str
    model: type
    label: str
    singular: str
    icon: str
    fields: list
    columns: list  # (attr, label)
    title_attr: str
    description: str = ""
    groups: list = field(default_factory=list)  # [(title, description, [field names])]


SKILL_CATEGORIES = ["Programming", "Web Development", "Broadcast Technology", "Video Editing",
                    "Cybersecurity", "Operating Systems", "Tools", "Productivity"]
PROFICIENCY = [("", "Not shown"), ("Learning", "Learning"), ("Familiar", "Familiar"),
               ("Intermediate", "Intermediate"), ("Proficient", "Proficient"), ("Advanced", "Advanced"), ("Expert", "Expert")]
SOCIAL_PLATFORMS = [(p, p.title()) for p in
                    ["github", "linkedin", "email", "x", "facebook", "instagram", "youtube",
                     "telegram", "whatsapp", "website"]]

RESOURCES: dict[str, Resource] = {r.key: r for r in [
    Resource("projects", Project, "Projects", "Project", "folder", [
        Field("title", "Project title", required=True),
        Field("slug", "URL slug", "slug", help="Used in /projects/<slug>. Leave blank to generate from the title."),
        Field("tagline", "Tagline", placeholder="One-line pitch"),
        Field("summary", "Card summary", "textarea", help="Short description shown on project cards."),
        Field("description", "Full description", "textarea", wide=True,
              help="Shown on the project page. Separate paragraphs with a blank line."),
        Field("highlights", "Key features", "lines", help="One per line."),
        Field("tech_stack", "Technology stack", "tags", help="Comma separated, e.g. Django, Python, PostgreSQL"),
        Field("thumbnail", "Thumbnail", "image", upload_dir="projects", max_dim=1600),
        Field("github_url", "GitHub URL", "url"),
        Field("demo_url", "Live demo URL", "url"),
        Field("status", "Status", "select", choices=Project.STATUSES),
        Field("featured", "Featured on homepage", "bool"),
        Field("visible", "Published", "bool"),
    ], [("title", "Title"), ("status_label", "Status"), ("featured", "Featured")], "title",
        "Showcase work with screenshots, links and tech tags."),
    Resource("skills", Skill, "Skills", "Skill", "layers", [
        Field("name", "Skill name", required=True),
        Field("category", "Category", "datalist", required=True, choices=SKILL_CATEGORIES,
              help="Pick one or type a new category."),
        Field("icon", "Icon", "icon",
              help="A built-in icon, or a brand logo as si:<slug> from simpleicons.org (e.g. si:python)."),
        Field("icon_image", "Custom icon image", "image", upload_dir="icons", max_dim=256,
              help="Optional - overrides the icon above."),
        Field("description", "Short description", "textarea"),
        Field("proficiency", "Proficiency (optional)", "select", choices=PROFICIENCY,
              help="Only shown if set. No percentages."),
        Field("years", "Years of experience (optional)", "float"),
        Field("visible", "Visible (confirmed skill)", "bool"),
    ], [("name", "Skill"), ("category", "Category"), ("proficiency", "Proficiency")], "name",
        "Only skills marked visible appear publicly."),
    Resource("experience", Experience, "Experience", "Experience", "briefcase", [
        Field("company", "Company", required=True),
        Field("position", "Position", required=True),
        Field("employment_type", "Employment type", placeholder="Full-time, Contract..."),
        Field("location", "Location"),
        Field("start_date", "Start (YYYY-MM)", "month"),
        Field("end_date", "End (YYYY-MM)", "month", help="Leave blank if current."),
        Field("is_current", "I currently work here", "bool"),
        Field("description", "Summary", "textarea", wide=True),
        Field("responsibilities", "Responsibilities", "lines", wide=True, help="One per line."),
        Field("achievements", "Achievements", "lines", wide=True, help="One per line. Only real ones!"),
        Field("technologies", "Technologies & equipment", "tags", help="Comma separated."),
        Field("logo", "Company logo", "image", upload_dir="logos", max_dim=400),
        Field("company_url", "Company website", "url"),
        Field("visible", "Visible", "bool"),
    ], [("position", "Position"), ("company", "Company"), ("start_date", "Start")], "position"),
    Resource("timeline", TimelineEvent, "Career Journey", "Milestone", "milestone", [
        Field("period", "Period / year", required=True, placeholder="2023 or 2022 - 2024"),
        Field("title", "Title", required=True),
        Field("kind", "Type", "select", choices=[("broadcast", "Broadcast"), ("development", "Development"),
                                                 ("security", "Security"), ("education", "Education"),
                                                 ("milestone", "Milestone")]),
        Field("description", "Description", "textarea"),
        Field("visible", "Visible", "bool"),
    ], [("period", "Period"), ("title", "Milestone"), ("kind", "Type")], "title",
        "The interactive timeline in the About section."),
    Resource("education", Education, "Education", "Education", "graduation", [
        Field("institution", "Institution", required=True),
        Field("degree", "Degree / programme", required=True),
        Field("field", "Field of study"),
        Field("start_date", "Start (YYYY-MM)", "month"),
        Field("end_date", "End (YYYY-MM)", "month"),
        Field("is_current", "Currently studying", "bool"),
        Field("description", "Details", "textarea", wide=True),
        Field("logo", "Logo", "image", upload_dir="logos", max_dim=400),
        Field("visible", "Visible", "bool"),
    ], [("degree", "Degree"), ("institution", "Institution")], "degree"),
    Resource("certifications", Certification, "Certifications & Awards", "Entry", "award", [
        Field("kind", "Type", "select", choices=[("certification", "Certification"), ("course", "Course"),
                                                 ("award", "Award / achievement")]),
        Field("name", "Name", required=True),
        Field("issuer", "Issuer / organisation"),
        Field("date", "Date (YYYY-MM)", "month"),
        Field("credential_url", "Credential URL", "url"),
        Field("description", "Description", "textarea"),
        Field("visible", "Visible", "bool"),
    ], [("name", "Name"), ("kind", "Type"), ("issuer", "Issuer")], "name"),
    Resource("socials", SocialLink, "Social Links", "Link", "link", [
        Field("platform", "Platform", "select", required=True, choices=SOCIAL_PLATFORMS),
        Field("label", "Label", placeholder="e.g. LinkedIn"),
        Field("handle", "Handle / display text", placeholder="@username"),
        Field("url", "URL", "url", required=True, help="https://... or mailto:you@example.com"),
        Field("visible", "Visible", "bool"),
    ], [("platform", "Platform"), ("handle", "Handle"), ("url", "URL")], "platform"),
]}


RESOURCE_GROUPS = {
    "projects": [
        ("Basics", "The title and short text shown on project cards.", ["title", "slug", "tagline", "summary"]),
        ("Case study", "The full write-up on the project's own page.", ["description", "highlights", "tech_stack"]),
        ("Links & media", "Buttons only appear when a link is filled in.", ["thumbnail", "github_url", "demo_url"]),
        ("Publishing", "Control where and whether the project appears.", ["status", "featured", "visible"]),
    ],
    "skills": [
        ("Skill", "What the skill is and where it is grouped.", ["name", "category", "description"]),
        ("Icon", "Shown on the skill card.", ["icon", "icon_image"]),
        ("Level (optional)", "Only shown when set. Never use percentages.", ["proficiency", "years"]),
        ("Publishing", "", ["visible"]),
    ],
    "experience": [
        ("Role", "Who you worked for and in what position.", ["company", "position", "employment_type", "location", "company_url"]),
        ("Dates", "Months are shown as e.g. \"Oct 2022\".", ["start_date", "end_date", "is_current"]),
        ("Details", "Keep each line short and specific.", ["description", "responsibilities", "achievements", "technologies"]),
        ("Media & publishing", "", ["logo", "visible"]),
    ],
    "timeline": [
        ("Milestone", "A point in your journey, shown in the About section.", ["period", "title", "kind", "description"]),
        ("Publishing", "", ["visible"]),
    ],
    "education": [
        ("Programme", "", ["degree", "field", "institution"]),
        ("Dates", "", ["start_date", "end_date", "is_current"]),
        ("Details", "Results, session or notes.", ["description", "logo", "visible"]),
    ],
    "certifications": [
        ("Certificate", "Certifications and courses appear under Certifications; awards appear separately.",
         ["kind", "name", "issuer", "date"]),
        ("Details", "", ["description", "credential_url", "visible"]),
    ],
    "socials": [
        ("Link", "Shown as cards in the contact banner and icons in the footer.",
         ["platform", "label", "handle", "url", "visible"]),
    ],
}
for _k, _g in RESOURCE_GROUPS.items():
    RESOURCES[_k].groups = _g


def field_groups(res) -> list:
    """Groups for a resource, with any ungrouped fields collected under "Other"."""
    by_name = {f.name: f for f in res.fields}
    out, used = [], set()
    for title, desc, names in res.groups or [("Details", "", [f.name for f in res.fields])]:
        fs = [by_name[n] for n in names if n in by_name]
        used.update(f.name for f in fs)
        out.append((title, desc, fs))
    rest = [f for f in res.fields if f.name not in used]
    if rest:
        out.append(("Other", "", rest))
    return out


def field_limits(model, fields) -> dict:
    return {f.name: _max_len(model, f.name) for f in fields
            if f.type not in ("bool", "image", "select", "float") and _max_len(model, f.name) < 20000}


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:150] or "project"


def _max_len(model, name):
    col = model.__table__.columns.get(name)
    if col is not None and isinstance(col.type, String) and col.type.length:
        return col.type.length
    return 20000


def apply_form(res: Resource, obj, form, files) -> dict:
    """Validate and copy form values onto ``obj``. Returns {field: error}."""
    errors = {}
    pending_uploads = []
    for f in res.fields:
        if f.type == "bool":
            setattr(obj, f.name, form.get(f.name) == "on")
            continue
        if f.type == "image":
            if form.get(f"{f.name}__remove") == "on":
                pending_uploads.append((f.name, None))
            fs = files.get(f.name)
            if fs and fs.filename:
                try:
                    pending_uploads.append((f.name, save_image(fs, f.upload_dir, f.max_dim)))
                except UploadError as e:
                    errors[f.name] = str(e)
            continue
        raw = (form.get(f.name) or "").replace("\r\n", "\n").strip()
        if f.required and not raw:
            errors[f.name] = f"{f.label} is required."
            continue
        if len(raw) > _max_len(res.model, f.name):
            errors[f.name] = f"{f.label} is too long."
            continue
        val = raw
        if raw:
            if f.type == "url":
                ok = URL_RE.match(raw) or (res.key == "socials" and raw.lower().startswith("mailto:")
                                           and EMAIL_RE.match(raw[7:]))
                if not ok:
                    errors[f.name] = "Enter a full URL starting with https://"
            elif f.type == "email" and not EMAIL_RE.match(raw):
                errors[f.name] = "Enter a valid email address."
            elif f.type == "month" and not MONTH_RE.match(raw):
                errors[f.name] = "Use YYYY or YYYY-MM."
            elif f.type == "select" and raw not in [c[0] for c in f.choices]:
                errors[f.name] = "Choose a valid option."
            elif f.type == "slug":
                val = slugify(raw)
            elif f.type == "icon" and not (raw in BUILTIN_SKILL_ICONS or re.match(r"^si:[a-z0-9]{1,40}$", raw)):
                errors[f.name] = "Choose a built-in icon or use si:<slug>."
            elif f.type == "float":
                try:
                    num = float(raw)
                    if not 0 <= num <= 60:
                        raise ValueError
                    val = num
                except ValueError:
                    errors[f.name] = "Enter a number between 0 and 60."
            elif f.type == "tags":
                val = ", ".join(t.strip() for t in raw.split(",") if t.strip())
        else:
            val = None if f.type == "float" else ""
        if f.name not in errors:
            setattr(obj, f.name, val)

    if res.key == "projects" and not errors:
        base = obj.slug or slugify(obj.title)
        slug, n = base, 2
        while Project.query.filter(Project.slug == slug, Project.id != (obj.id or 0)).first():
            slug, n = f"{base}-{n}", n + 1
        obj.slug = slug

    if errors:
        for _, path in pending_uploads:
            delete_upload(path)
    else:
        for name, path in pending_uploads:
            old = getattr(obj, name)
            in_gallery = isinstance(obj, Project) and any(i.path == old for i in obj.images)
            if old and old != path and not in_gallery:
                delete_upload(old)
            setattr(obj, name, path or "")
    return errors


def _res(key) -> Resource:
    res = RESOURCES.get(key)
    if res is None:
        abort(404)
    return res


# ------------------------------------------------------------------ dashboard
@bp.route("/")
def dashboard():
    d_pub = design_mod.get_published()
    prof = Profile.get()
    sections = [s for s in d_pub["sections"]]
    checks = [
        ("Profile name and introduction", bool(prof.full_name and prof.short_intro)),
        ("Profile photo uploaded", bool(prof.avatar)),
        ("Contact email set", bool(prof.email)),
        ("At least one social link", SocialLink.published().count() > 0),
        ("Confirmed skills visible", Skill.published().count() > 0),
        ("Experience published", Experience.published().count() > 0),
        ("Education published", Education.published().count() > 0),
        ("GitHub username connected", bool(prof.github_username)),
        ("CV / resume uploaded", bool(prof.resume)),
    ]
    stats = [
        ("Projects", Project.query.count(), Project.published().count(), "projects", "folder"),
        ("Skills", Skill.query.count(), Skill.published().count(), "skills", "layers"),
        ("Experience", Experience.query.count(), Experience.published().count(), "experience", "briefcase"),
        ("Milestones", TimelineEvent.query.count(), TimelineEvent.published().count(), "timeline", "milestone"),
    ]
    return render_template(
        "admin/dashboard.html", stats=stats, checks=checks,
        sections=sections, published_sections=sum(1 for s in sections if s["enabled"]),
        drafts_pending=design_mod.has_unpublished_changes(),
        recent_messages=Message.query.order_by(Message.created_at.desc()).limit(5).all(),
        hidden_skills=Skill.query.filter_by(visible=False).count(),
    )


# ------------------------------------------------------------------ generic CRUD
@bp.route("/r/<key>")
def resource_list(key):
    res = _res(key)
    items = res.model.ordered().all()
    return render_template("admin/list.html", res=res, items=items)


@bp.route("/r/<key>/new", methods=["GET", "POST"])
@bp.route("/r/<key>/<int:item_id>/edit", methods=["GET", "POST"])
def resource_edit(key, item_id=None):
    res = _res(key)
    obj = db.session.get(res.model, item_id) if item_id else None
    if item_id and obj is None:
        abort(404)
    is_new = obj is None
    errors = {}
    if is_new:
        obj = res.model()
        if request.method == "GET":
            for f in res.fields:
                if f.type == "bool":
                    setattr(obj, f.name, f.name == "visible")
    if request.method == "POST":
        errors = apply_form(res, obj, request.form, request.files)
        if not errors:
            if is_new:
                obj.sort_order = (db.session.query(db.func.max(res.model.sort_order)).scalar() or 0) + 1
                db.session.add(obj)
            db.session.commit()
            flash(f"{res.singular} saved.", "success")
            if request.form.get("_continue") or (is_new and key == "projects"):
                return redirect(url_for("admin.resource_edit", key=key, item_id=obj.id))
            return redirect(url_for("admin.resource_list", key=key))
        flash("Please fix the errors below.", "error")
    with db.session.no_autoflush:  # never flush half-validated edits
        html = render_template("admin/edit.html", res=res, obj=obj, errors=errors, is_new=is_new,
                               groups=field_groups(res), limits=field_limits(res.model, res.fields),
                               builtin_icons=BUILTIN_SKILL_ICONS)
    if errors:
        db.session.rollback()
        return html, 422
    return html


@bp.route("/r/<key>/<int:item_id>/delete", methods=["POST"])
def resource_delete(key, item_id):
    res = _res(key)
    obj = db.session.get(res.model, item_id) or abort(404)
    for f in res.fields:
        if f.type == "image":
            delete_upload(getattr(obj, f.name))
    if isinstance(obj, Project):  # gallery files (thumbnail may be one of them)
        for img in obj.images:
            delete_upload(img.path)
    db.session.delete(obj)
    db.session.commit()
    flash(f"{res.singular} deleted.", "success")
    return redirect(url_for("admin.resource_list", key=key))


@bp.route("/r/<key>/<int:item_id>/toggle", methods=["POST"])
def resource_toggle(key, item_id):
    res = _res(key)
    obj = db.session.get(res.model, item_id) or abort(404)
    attr = request.form.get("attr", "visible")
    if attr not in ("visible", "featured") or not hasattr(obj, attr):
        abort(400)
    setattr(obj, attr, not getattr(obj, attr))
    db.session.commit()
    if request.accept_mimetypes.best == "application/json":
        return {"ok": True, "value": getattr(obj, attr)}
    return redirect(url_for("admin.resource_list", key=key))


@bp.route("/r/<key>/reorder", methods=["POST"])
def resource_reorder(key):
    res = _res(key)
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids")
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        return {"ok": False, "error": "Invalid order."}, 400
    items = {o.id: o for o in res.model.query.filter(res.model.id.in_(ids)).all()}
    for pos, i in enumerate(ids):
        if i in items:
            items[i].sort_order = pos
    db.session.commit()
    return {"ok": True}


@bp.route("/r/<key>/<int:item_id>/move/<direction>", methods=["POST"])
def resource_move(key, item_id, direction):
    res = _res(key)
    items = res.model.ordered().all()
    idx = next((i for i, o in enumerate(items) if o.id == item_id), None)
    if idx is None:
        abort(404)
    swap = idx - 1 if direction == "up" else idx + 1
    if 0 <= swap < len(items):
        items[idx], items[swap] = items[swap], items[idx]
    for pos, o in enumerate(items):
        o.sort_order = pos
    db.session.commit()
    return redirect(url_for("admin.resource_list", key=key))


# ------------------------------------------------------------------ project gallery
@bp.route("/projects/<int:pid>/images", methods=["POST"])
def project_images_upload(pid):
    project = db.session.get(Project, pid) or abort(404)
    saved, failed = 0, []
    start = len(project.images)
    for i, fs in enumerate(request.files.getlist("images")[:12]):
        if not fs or not fs.filename:
            continue
        try:
            path = save_image(fs, "projects", 1920)
            project.images.append(ProjectImage(path=path, sort_order=start + i))
            saved += 1
        except UploadError as e:
            failed.append(f"{fs.filename[:40]}: {e}")
    db.session.commit()
    if saved:
        flash(f"Uploaded {saved} image(s).", "success")
    for f in failed:
        flash(f, "error")
    return redirect(url_for("admin.resource_edit", key="projects", item_id=pid, _anchor="gallery"))


@bp.route("/projects/<int:pid>/images/<int:img_id>", methods=["POST"])
def project_image_update(pid, img_id):
    img = db.session.get(ProjectImage, img_id)
    if img is None or img.project_id != pid:
        abort(404)
    action = request.form.get("action")
    if action == "delete":
        if img.project.thumbnail != img.path:  # still used as the thumbnail
            delete_upload(img.path)
        db.session.delete(img)
        flash("Image removed.", "success")
    elif action == "cover":
        img.project.thumbnail = img.path
        flash("Set as thumbnail.", "success")
    else:
        img.caption = (request.form.get("caption") or "").strip()[:200]
        flash("Caption saved.", "success")
    db.session.commit()
    return redirect(url_for("admin.resource_edit", key="projects", item_id=pid, _anchor="gallery"))


# ------------------------------------------------------------------ profile
PROFILE_GROUPS = [
    ("Identity", "How your name and title appear across the site.", [
        Field("full_name", "Full name", required=True, placeholder="Sanjidur Rahman Sanjid",
              help="Used in the hero, access pass, footer and browser tab."),
        Field("short_name", "Short name", placeholder="Sanjid",
              help="Used in the logo, the hero terminal and the lanyard."),
        Field("headline", "Professional title", required=True,
              help="One line shown in the footer and search results."),
        Field("rotating_titles", "Hero roles", "lines",
              help="Up to 4 shown under your name, each with an icon (icons are set in Site Content → Hero)."),
    ]),
    ("Introduction", "The story visitors read about you.", [
        Field("short_intro", "Hero introduction", "textarea", required=True,
              help="Two or three sentences under your name."),
        Field("about", "About me", "textarea", wide=True,
              help="The first paragraph becomes the large opening line. Separate paragraphs with a blank line. "
                   "Wrap words in *asterisks* to highlight them."),
        Field("career_goals", "Career goal", "textarea", help="Shown in the \"Where I'm headed\" card."),
    ]),
    ("Contact & presence", "Where people can reach you. Leave a field empty to hide it.", [
        Field("email", "Public email", "email", placeholder="name@example.com"),
        Field("phone", "Phone", placeholder="+880 ...", help="Shown publicly in the contact section."),
        Field("location", "Location", placeholder="Dhaka, Bangladesh",
              help="The first part (before the comma) is used on the access pass."),
        Field("availability", "Availability status", placeholder="Open to new opportunities",
              help="Shown in the hero and the contact banner."),
        Field("github_username", "GitHub username", "github", placeholder="sanjidmolik",
              help="Powers the GitHub dashboard and access pass handle."),
    ]),
    ("Search & sharing", "How your portfolio appears in Google and link previews.", [
        Field("seo_title", "SEO title", help="Aim for 50-60 characters."),
        Field("seo_description", "SEO description", "textarea", help="Aim for 140-160 characters."),
    ]),
]
PROFILE_FIELDS = [f for _, _, fs in PROFILE_GROUPS for f in fs]


@bp.route("/profile", methods=["GET", "POST"])
def profile():
    prof = Profile.get()
    errors = {}
    if request.method == "POST":
        for f in PROFILE_FIELDS:
            val = (request.form.get(f.name) or "").replace("\r\n", "\n").strip()
            limit = _max_len(Profile, f.name)
            if f.required and not val:
                errors[f.name] = f"{f.label} is required."
            elif len(val) > limit:
                errors[f.name] = f"{f.label} must be {limit} characters or fewer (currently {len(val)})."
            elif f.type == "email" and val and not EMAIL_RE.match(val):
                errors[f.name] = "Enter a valid email address, e.g. name@example.com."
            elif f.type == "github" and val and not re.match(r"^[A-Za-z0-9-]{1,39}$", val):
                errors[f.name] = "Enter just the username (letters, numbers and hyphens), e.g. octocat."
            setattr(prof, f.name, val)  # keep typed values for re-display; rolled back on error
        uploads = []
        if request.form.get("avatar__remove") == "on":
            uploads.append(("avatar", None))
        if request.form.get("resume__remove") == "on":
            uploads.append(("resume", None))
        if request.form.get("hero_image__remove") == "on":
            uploads.append(("hero_image", None))
        try:
            fs = request.files.get("avatar")
            if fs and fs.filename:
                uploads.append(("avatar", save_image(fs, "profile", 900)))
            fs = request.files.get("hero_image")
            if fs and fs.filename:
                uploads.append(("hero_image", save_image(fs, "profile", 1400)))
            fs = request.files.get("resume")
            if fs and fs.filename:
                uploads.append(("resume", save_pdf(fs)))
        except UploadError as e:
            errors["upload"] = str(e)
        if errors:
            for _, p in uploads:
                delete_upload(p)
            flash("Please fix the errors below.", "error")
            with db.session.no_autoflush:
                html = render_template("admin/profile.html", prof=prof, groups=PROFILE_GROUPS, errors=errors,
                                       limits=field_limits(Profile, PROFILE_FIELDS))
            db.session.rollback()
            return html, 422
        else:
            for name, path in uploads:
                if getattr(prof, name) and getattr(prof, name) != path:
                    delete_upload(getattr(prof, name))
                setattr(prof, name, path or "")
            db.session.commit()
            flash("Profile saved.", "success")
            return redirect(url_for("admin.profile"))
    return render_template("admin/profile.html", prof=prof, groups=PROFILE_GROUPS, errors=errors,
                           limits=field_limits(Profile, PROFILE_FIELDS))


# ------------------------------------------------------------------ site content
@bp.route("/content", methods=["GET", "POST"])
def site_content():
    from . import site_content as sc
    values, errors = sc.get_content(), {}
    if request.method == "POST":
        values, errors = sc.validate(request.form)
        if errors:
            flash(f"Please fix {len(errors)} field(s) below.", "error")
        else:
            sc.save_content(values)
            flash("Site content saved. Changes are live on your portfolio.", "success")
            return redirect(url_for("admin.site_content", _anchor=request.form.get("_tab") or ""))
    return render_template("admin/content.html", groups=sc.GROUPS, values=values, errors=errors,
                           defaults=sc.defaults(), builtin_icons=BUILTIN_SKILL_ICONS), (422 if errors else 200)


# ------------------------------------------------------------------ messages
@bp.route("/messages")
def messages():
    items = Message.query.order_by(Message.created_at.desc()).all()
    return render_template("admin/messages.html", items=items)


@bp.route("/messages/<int:mid>", methods=["POST"])
def message_action(mid):
    msg = db.session.get(Message, mid) or abort(404)
    action = request.form.get("action")
    if action == "delete":
        db.session.delete(msg)
        flash("Message deleted.", "success")
    elif action == "unread":
        msg.is_read = False
    else:
        msg.is_read = True
    db.session.commit()
    return redirect(url_for("admin.messages"))


# ------------------------------------------------------------------ design center
@bp.route("/design")
def design():
    return render_template("admin/design.html", draft=design_mod.get_draft(),
                           published=design_mod.get_published(), fonts=list(design_mod.FONTS),
                           choices=design_mod.CHOICES, defaults=design_mod.default_design(),
                           presets=design_mod.preset_designs(), font_css=design_mod.FONTS,
                           dirty=design_mod.has_unpublished_changes())


@bp.route("/design/draft", methods=["POST"])
def design_save_draft():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return {"ok": False, "error": "Invalid design payload."}, 400
    clean = design_mod.save_draft(payload)
    return {"ok": True, "design": clean, "dirty": design_mod.has_unpublished_changes()}


@bp.route("/design/publish", methods=["POST"])
def design_publish():
    payload = request.get_json(silent=True)
    clean = design_mod.publish(payload if isinstance(payload, dict) else None)
    current_app.logger.info("Design published by %s", current_admin().username)
    return {"ok": True, "design": clean, "dirty": False}


@bp.route("/design/reset", methods=["POST"])
def design_reset():
    clean = design_mod.save_draft(design_mod.default_design())
    return {"ok": True, "design": clean, "dirty": design_mod.has_unpublished_changes()}


@bp.route("/design/discard", methods=["POST"])
def design_discard():
    clean = design_mod.save_draft(design_mod.get_published())
    return {"ok": True, "design": clean, "dirty": False}


# ------------------------------------------------------------------ github + account
@bp.route("/github/refresh", methods=["POST"])
def github_refresh():
    data = get_github_data(Profile.get().github_username, force=True)
    flash("GitHub data refreshed." if data else "Could not fetch GitHub data. Check the username.",
          "success" if data else "error")
    return redirect(request.referrer if (request.referrer or "").startswith(request.host_url)
                    else url_for("admin.dashboard"))


@bp.route("/account", methods=["GET", "POST"])
def account():
    user = current_admin()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "revoke":
            user.session_version += 1
            db.session.commit()
            session.clear()
            flash("All sessions were signed out.", "success")
            return redirect(url_for("auth.login"))
        current = request.form.get("current_password") or ""
        new = request.form.get("new_password") or ""
        confirm = request.form.get("confirm_password") or ""
        if not user.check_password(current):
            flash("Current password is incorrect.", "error")
        elif new != confirm:
            flash("New passwords don't match.", "error")
        elif (err := validate_password(new)):
            flash(err, "error")
        else:
            user.set_password(new)
            user.session_version += 1
            db.session.commit()
            session["admin_ver"] = user.session_version  # keep this session, revoke others
            flash("Password changed. Other sessions were signed out.", "success")
            return redirect(url_for("admin.account"))
    return render_template("admin/account.html", user=user)


@bp.route("/design/compile", methods=["POST"])
def design_compile():
    """Turn an unsaved design into CSS for the live-preview iframe (nothing is stored)."""
    payload = request.get_json(silent=True)
    clean = design_mod.sanitize(payload if isinstance(payload, dict) else {})
    return {"ok": True, "css": design_mod.css_variables(clean), "classes": design_mod.body_classes(clean),
            "font_url": design_mod.font_url(clean), "mode": clean["theme"]["mode"],
            "allow_toggle": clean["theme"]["allow_toggle"], "sections": clean["sections"]}
