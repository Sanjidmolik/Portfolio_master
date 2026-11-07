"""Editable site copy (labels, headings, button text...) managed from /admin/content.

Every visible string on the public site that isn't already a model field or a
Design Center setting lives here. Values are validated against this schema
(known keys only, length limits, required fields, icon whitelist) before they
are stored, and rendered with Jinja autoescaping.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .icons import BUILTIN_SKILL_ICONS
from .models import Setting

KEY = "site_content"
ICON_RE = re.compile(r"^si:[a-z0-9]{1,40}$")


@dataclass(frozen=True)
class CField:
    key: str
    label: str
    default: str
    max: int = 80
    required: bool = False
    kind: str = "text"  # text | textarea | icon
    help: str = ""
    example: str = ""


def _roles():
    out = []
    for i, icon in enumerate(["monitor", "code", "shield", "graduation"], 1):
        out.append(CField(f"hero_role{i}_icon", f"Role {i} icon", icon, 44, kind="icon",
                          help=f"Icon for line {i} of \"Hero roles\" in Profile."))
    return out


def _stats():
    out = []
    for i, (icon, title, sub) in enumerate([("broadcast", "3+ Years", "Broadcast Experience"),
                                            ("code", "Passionate", "Developer"),
                                            ("shield", "Cybersecurity", "Learner")], 1):
        out += [CField(f"hero_stat{i}_icon", f"Highlight {i}: icon", icon, 44, kind="icon"),
                CField(f"hero_stat{i}_title", f"Highlight {i}: title", title, 24,
                       help="Leave empty to hide this highlight."),
                CField(f"hero_stat{i}_sub", f"Highlight {i}: caption", sub, 30)]
    return out


def _focus():
    out = []
    for i, (icon, title, text) in enumerate([
        ("broadcast", "Broadcast Ops", "MCR, playout & signal quality"),
        ("code", "Software", "Python and the web"),
        ("shield", "Cybersecurity", "Security fundamentals"),
        ("graduation", "CSE Student", "Eastern University"),
    ], 1):
        out += [CField(f"focus{i}_icon", f"Focus card {i}: icon", icon, 44, kind="icon"),
                CField(f"focus{i}_title", f"Focus card {i}: title", title, 28,
                       help="Leave empty to hide this card."),
                CField(f"focus{i}_text", f"Focus card {i}: description", text, 60)]
    return out


GROUPS = [
    {"key": "hero", "title": "Hero", "icon": "sparkles",
     "intro": ("The first screen visitors see. Your name, roles (\"Hero roles\"), introduction and hero portrait "
               "are edited in Profile; the \"Currently at\" card uses your current job from Experience."),
     "fields": [
         CField("hero_badge", "Live badge", "LIVE", 12, True, help="Red label at the top of the hero."),
         CField("hero_badge_sub", "Live badge caption", "24/7 ON AIR", 24, help="Shown after the divider."),
         CField("hero_greeting", "Greeting", "Hello, I'm", 40, True, help="Shown directly above your name."),
         *_roles(),
         CField("hero_cta_primary", "Primary button", "Explore My Work", 30, True,
                help="Scrolls to your projects."),
         CField("hero_cta_secondary", "Secondary button", "Contact Me", 30, True,
                help="Scrolls to the contact section."),
         CField("hero_cv_label", "CV button", "Download CV", 20, help="Only shown when a CV PDF is uploaded in Profile."),
         *_stats(),
         CField("hero_current_label", "\"Currently at\" label", "Currently at", 24,
                help="The card is hidden when no current job is marked in Experience."),
         CField("hero_since_label", "\"Since\" word", "Since", 12),
         CField("hero_scene_sign", "Studio sign", "ON AIR", 10, help="The neon sign in the control-room scene."),
         CField("hero_scroll", "Scroll hint", "Scroll Down", 20),
         CField("hero_tagline", "Tagline (bottom right)", "BROADCAST • CODE • INNOVATE", 50),
     ]},
    {"key": "about", "title": "About", "icon": "user",
     "intro": "Your About text and career goal are edited in Profile. These are the labels and cards around them.",
     "fields": [
         CField("about_goal_label", "Career goal label", "WHERE I'M HEADED", 30),
         CField("about_since_label", "Tile: start year label", "ON AIR SINCE", 24),
         CField("about_since_sub", "Tile: start year caption", "Broadcast operations", 40),
         CField("about_tile_value", "Tile: highlight value", "24/7", 10, True, example="24/7"),
         CField("about_tile_label", "Tile: highlight label", "CONTROL ROOM", 24),
         CField("about_tile_sub", "Tile: highlight caption", "Live transmission", 40),
         CField("about_now_label", "Tile: current role label", "NOW", 16),
         CField("about_study_label", "Tile: studies label", "STUDYING", 16),
         CField("about_stack_label", "Tile: stack label", "CORE STACK", 20,
                help="The chips come from your visible skills in the Programming category."),
         *_focus(),
         CField("about_journey_title", "Journey heading", "My journey", 40, True),
     ]},
    {"key": "pass", "title": "Access pass", "icon": "lock",
     "intro": "The lanyard ID card in the GitHub section. Role, station and study come from Experience and Education.",
     "fields": [
         CField("pass_header", "Card header", "BROADCAST ACCESS PASS", 28, True),
         CField("pass_zone", "Zone tag", "MCR", 8),
         CField("pass_stamp", "Stamp text", "ON AIR", 10, help="Shown on two lines inside the round stamp."),
         CField("pass_lanyard", "Lanyard text", "", 60, help="Leave empty to generate it from your short name."),
         CField("pass_station_label", "Label: station", "STATION", 16),
         CField("pass_base_label", "Label: base", "BASE", 16),
         CField("pass_study_label", "Label: study", "STUDY", 16),
         CField("pass_since_label", "Label: start year", "ON AIR SINCE", 16),
         CField("pass_on_duty", "Status when employed", "ON DUTY", 16),
         CField("pass_available", "Status otherwise", "AVAILABLE", 16),
     ]},
    {"key": "github", "title": "GitHub dashboard", "icon": "github",
     "intro": "Statistics are loaded live from GitHub; these are the headings.",
     "fields": [
         CField("gh_eyebrow", "Eyebrow", "// SIGNAL REPORT", 30),
         CField("gh_top_label", "Top repositories heading", "TOP REPOSITORIES · STARS", 40),
         CField("gh_latest_label", "Latest repositories heading", "LATEST REPOSITORIES", 40,
                help="Used instead of the chart while none of your repositories have stars."),
         CField("gh_channels_label", "Skill categories heading", "FREQUENCIES", 30),
         CField("gh_languages_label", "Languages heading", "LANGUAGES ON GITHUB", 30),
         CField("gh_unavailable", "Message when GitHub is unreachable", "GitHub activity is temporarily unavailable.", 120),
     ]},
    {"key": "education", "title": "Education & certificates", "icon": "graduation",
     "intro": "Headings and filter labels. The entries themselves are managed in Education and Certifications & Awards.",
     "fields": [
         CField("edu_heading", "Education heading", "EDUCATION", 30, True),
         CField("certs_heading", "Certificates heading", "CERTIFICATIONS & AWARDS", 40, True),
         CField("cert_filter_all", "Filter: all", "All", 20, True),
         CField("cert_filter_certification", "Filter / badge: certifications", "Certifications", 24, True),
         CField("cert_filter_course", "Filter / badge: courses", "Courses", 24, True),
         CField("cert_filter_award", "Filter / badge: awards", "Awards", 24, True),
         CField("cert_view_link", "Credential link text", "View credential", 24, True),
     ]},
    {"key": "contact", "title": "Contact", "icon": "mail",
     "intro": "Email, phone, location and social links are edited in Profile and Social Links.",
     "fields": [
         CField("contact_banner_eyebrow", "Banner eyebrow", "// OPEN A CHANNEL", 30),
         CField("contact_banner_title", "Banner heading", "Let's put something great on air", 70, True),
         CField("contact_lead", "Intro paragraph", ("Whether it's a broadcast operations role, a software project "
                                                     "or a security opportunity, send a message and I'll get back to you."),
                300, kind="textarea"),
         CField("contact_form_heading", "Form heading", "NEW TRANSMISSION", 30),
         CField("contact_name_label", "Field label: name", "Your name", 30, True),
         CField("contact_email_label", "Field label: email", "Email address", 30, True),
         CField("contact_subject_label", "Field label: subject", "Subject (optional)", 30, True),
         CField("contact_message_label", "Field label: message", "Your message", 30, True),
         CField("contact_button", "Send button", "Send message", 24, True),
         CField("contact_success", "Success message", "Thanks! Your message has been sent. I'll get back to you soon.",
                160, True, kind="textarea", help="Shown after a visitor sends the form."),
         CField("nav_cta", "Navigation contact button", "Hire Me", 16, True),
         CField("nav_brand_sub", "Logo subtitle", "Portfolio", 20, help="Small text under your short name in the top-left logo."),
     ]},
    {"key": "pages", "title": "Pages & footer", "icon": "file",
     "intro": "The projects archive page, project case studies and the footer.",
     "fields": [
         CField("projects_page_title", "Projects page title", "All Projects", 50, True),
         CField("projects_page_intro", "Projects page intro",
                "Everything I've built, from learning experiments to full applications.", 200, kind="textarea"),
         CField("projects_empty", "No projects message", "Projects are on their way. Check back soon.", 120),
         CField("projects_view_all", "\"View all\" button", "View all projects", 30, True,
                help="The project count is added automatically."),
         CField("project_case_label", "Case study label", "CASE STUDY", 20),
         CField("project_card_link", "Project card link", "Case study", 20, True),
         CField("project_features_label", "Key features heading", "KEY FEATURES", 24),
         CField("project_more_label", "More projects heading", "MORE PROJECTS", 24),
         CField("footer_status", "Footer status text", "Signal stable", 30),
     ]},
]

FIELDS = {f.key: f for g in GROUPS for f in g["fields"]}


def defaults() -> dict:
    return {k: f.default for k, f in FIELDS.items()}


def validate(form) -> tuple[dict, dict]:
    """Return (clean values, errors) for submitted form data. Unknown keys are ignored."""
    clean, errors = {}, {}
    for key, f in FIELDS.items():
        raw = form.get(key)
        val = " ".join(raw.split()) if (raw is not None and f.kind != "textarea") else (raw or "").replace("\r\n", "\n").strip()
        if f.required and not val:
            errors[key] = f"{f.label} is required."
        elif len(val) > f.max:
            errors[key] = f"{f.label} must be {f.max} characters or fewer (currently {len(val)})."
        elif f.kind == "icon" and val and not (val in BUILTIN_SKILL_ICONS or ICON_RE.match(val)):
            errors[key] = "Choose a built-in icon or use si:<slug> (lowercase letters and numbers)."
        clean[key] = val
    return clean, errors


def get_content() -> dict:
    stored = Setting.read(KEY) or {}
    out = defaults()
    for k, v in stored.items():
        if k in FIELDS and isinstance(v, str):
            out[k] = v[:FIELDS[k].max]
    return out


def save_content(values: dict) -> None:
    Setting.write(KEY, {k: v for k, v in values.items() if k in FIELDS})
