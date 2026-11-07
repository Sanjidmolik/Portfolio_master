"""Initial content.

Only facts already present in the original site or provided by the owner are
published. Everything else is seeded as a *hidden draft* (visible=False) so it
never appears publicly until the owner reviews and confirms it in /admin.
"""
from __future__ import annotations

import json
from pathlib import Path

from flask import current_app

from . import design
from .config import BASE_DIR
from .extensions import db
from .models import (Education, Experience, Message, Profile, Project, Setting, Skill,
                     TimelineEvent)

ABOUT = """I work in broadcast operations, where I monitor and support live television transmission from the Master Control Room (MCR). It's a 24/7 environment that has taught me to stay calm under pressure, think systematically and fix problems fast, because on-air mistakes are visible to everyone.

Alongside broadcasting I build software. I started learning to code in 2023 with Python, HTML, CSS and JavaScript, and I've since moved on to web frameworks like Django.

I'm also on a cybersecurity learning journey, exploring information security, network security, OSINT and digital forensics, and I'm studying Computer Science & Engineering."""

GOALS = ("My goal is to grow into a full-stack developer with strong security foundations, "
         "building real-world software that helps people, and bringing the reliability mindset "
         "of broadcast operations into everything I ship.")

SKILLS = [
    # (name, category, icon, description)
    ("Python", "Programming", "si:python", "Scripting, automation and back-end development."),
    ("JavaScript", "Programming", "si:javascript", "Interactive front-end behaviour."),
    ("HTML", "Programming", "si:html5", "Semantic, accessible markup."),
    ("CSS", "Programming", "si:css", "Layouts, theming and animation."),
    ("Django", "Web Development", "si:django", "Full-stack Python web applications."),
    ("Next.js", "Web Development", "si:nextdotjs", "React framework for production web apps."),
    ("React", "Web Development", "si:react", "Component-driven user interfaces."),
    ("REST APIs", "Web Development", "api", "Designing and consuming HTTP APIs."),
    ("Information Security", "Cybersecurity", "shield", "Core security principles and practices."),
    ("Network Security", "Cybersecurity", "network", "Protecting networks and traffic."),
    ("OSINT", "Cybersecurity", "search", "Open-source intelligence gathering."),
    ("Digital Forensics", "Cybersecurity", "fingerprint", "Investigating digital evidence."),
    ("MCR Operations", "Broadcast Technology", "broadcast", "24/7 master control room operations."),
    ("Aveco Astra", "Broadcast Technology", "playout", "Broadcast automation and playout."),
    ("Ross Production Systems", "Broadcast Technology", "monitor", "Live production systems."),
    ("OBS", "Broadcast Technology", "si:obsstudio", "Streaming and recording."),
    ("Broadcast Signal Monitoring", "Broadcast Technology", "signal", "Signal quality and compliance monitoring."),
    ("Git", "Tools", "si:git", "Version control."),
    ("GitHub", "Tools", "si:github", "Collaboration and code hosting."),
    ("VS Code", "Tools", "code", "Primary code editor."),
    ("Cursor", "Tools", "si:cursor", "AI-assisted code editor."),
]


def seed_if_empty() -> bool:
    """Seed initial content once. Returns True if anything was created."""
    if Profile.query.first() is not None:
        return False

    db.session.add(Profile(
        full_name="Sanjidur Rahman Sanjid",
        short_name="Sanjid",
        headline="Broadcast Operations Professional & Software Developer",
        rotating_titles="Broadcast Operations Professional\nSoftware Developer\n"
                        "Cybersecurity Enthusiast\nCSE Student",
        short_intro=("I keep live broadcasts on air from the Master Control Room, and I build "
                     "software with Python and the web, while learning cybersecurity and "
                     "studying Computer Science & Engineering."),
        about=ABOUT,
        career_goals=GOALS,
        seo_title="Sanjidur Rahman Sanjid | Broadcast Operations & Software Developer",
        seo_description=("Portfolio of Sanjidur Rahman Sanjid: broadcast operations professional, "
                         "software developer, cybersecurity enthusiast and CSE student."),
    ))

    # Journey: only "started coding in 2023" comes from the original site; the
    # rest are hidden drafts the owner needs to date and confirm.
    for i, (period, title, kind, desc, visible) in enumerate([
        ("2023", "Started writing code", "development",
         "Began learning Python, HTML, CSS and JavaScript and built my first website.", True),
        ("Add year", "Joined broadcast operations", "broadcast",
         "Started working in a Master Control Room environment.", False),
        ("Add year", "Began B.Sc. in Computer Science & Engineering", "education", "", False),
        ("Add year", "Started my cybersecurity journey", "security",
         "Exploring information security, network security, OSINT and digital forensics.", False),
        ("Add year", "Built CyberQuest", "development",
         "A gamified cybersecurity learning simulation built with Django.", False),
    ]):
        db.session.add(TimelineEvent(period=period, title=title, kind=kind, description=desc,
                                     visible=visible, sort_order=i))

    db.session.add(Experience(
        company="Company name (edit me)",
        position="Broadcast Operations - Master Control Room",
        is_current=True,
        description="Hidden draft: add your employer, dates and details, then make it visible.",
        responsibilities="\n".join([
            "24/7 broadcast operations in the Master Control Room",
            "Live transmission monitoring",
            "Operating playout systems",
            "Signal quality monitoring",
            "Broadcast troubleshooting and incident response",
        ]),
        technologies="Aveco Astra, Ross Production Systems, OBS",
        visible=False,
    ))

    db.session.add(Education(
        institution="University name (edit me)",
        degree="B.Sc. in Computer Science & Engineering",
        is_current=True,
        description="Hidden draft: add your university and dates, then make it visible.",
        visible=False,
    ))

    for i, (name, cat, icon, desc) in enumerate(SKILLS):
        db.session.add(Skill(name=name, category=cat, icon=icon, description=desc,
                             sort_order=i, visible=False))

    db.session.add(Project(
        title="CyberQuest",
        slug="cyberquest",
        tagline="A gamified cybersecurity learning simulation",
        summary=("An educational simulation platform that teaches cybersecurity through "
                 "interactive, game-like challenges."),
        description=("CyberQuest is a cybersecurity educational simulation platform built with "
                     "Django. Instead of reading theory, learners work through interactive "
                     "scenarios that make security concepts practical.\n\n"
                     "The experience is gamified so that progress feels rewarding and learners "
                     "stay motivated as the challenges get harder."),
        highlights="Interactive cybersecurity learning\nGamified learning experience\nDjango-based development",
        tech_stack="Django, Python, HTML, CSS, JavaScript",
        status="in-progress",
        featured=True,
        visible=True,
        sort_order=0,
    ))

    db.session.commit()
    if Setting.read(design.PUBLISHED_KEY) is None:
        design.publish(design.default_design())
    import_legacy_messages()
    from .cv_content import sync_cv_content
    sync_cv_content()
    return True


def import_legacy_messages() -> int:
    """Import messages saved by the original Flask app (messages.json)."""
    path = Path(BASE_DIR) / "messages.json"
    if not path.exists():
        return 0
    try:
        items = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    n = 0
    for m in items if isinstance(items, list) else []:
        if isinstance(m, dict) and m.get("message"):
            db.session.add(Message(name=str(m.get("name", ""))[:120] or "Unknown",
                                   email=str(m.get("email", ""))[:200],
                                   body=str(m["message"])[:5000]))
            n += 1
    db.session.commit()
    path.rename(path.with_suffix(".json.imported"))
    current_app.logger.info("Imported %d legacy messages", n)
    return n
