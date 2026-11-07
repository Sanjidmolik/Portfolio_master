"""Portfolio content taken from the owner's CV ("Sanjidur Rahman Sanjid MCR.pdf").

Applied by ``sync_cv_content()`` - on first start (from ``seed_if_empty``) and via
``flask --app app sync-cv``. It is idempotent: existing rows are matched and
updated, and the owner's choices about which existing skills are visible are
never changed.

Personal details on the CV (phone number, home address, parents' names, date
of birth, religion, marital status, height) are deliberately NOT published.
"""
from __future__ import annotations

from .extensions import db
from .models import (Certification, Education, Experience, Profile, Project, Skill, SocialLink,
                     TimelineEvent)

ABOUT = """I keep *live television on air*, and I build software with the same discipline.

As an MCR Executive at Channel One News, I operate the switching, playout and graphics systems behind every broadcast, monitor signal quality and compliance, and troubleshoot faults so programmes go out on time. Before that, I spent over three years in the Master Control Room at Asian Telecast Ltd.

A 24/7 control room teaches you to *stay calm under pressure*, follow the contingency plan and restore service fast. I bring that same mindset to code. I work mainly in Python, with Java and C, and I build for the web with HTML, CSS and JavaScript.

Right now I'm studying for a B.Sc. in Computer Science & Engineering at Eastern University and exploring cybersecurity along the way. I work in Bengali and English."""

INTRO = ("MCR Executive with three years of broadcast operations experience, keeping live "
         "transmission on air from the Master Control Room. I also build software with Python "
         "and the web, and I'm studying Computer Science & Engineering at Eastern University.")

TITLES = "\n".join([
    "Broadcast Operations Professional",
    "Software Developer",
    "Cybersecurity Enthusiast",
    "CSE Student",
])

EMAIL = "sanjid.molik123@gmail.com"
GITHUB = "sanjidmolik"

RESPONSIBILITIES = "\n".join([
    "Oversee Master Control Room (MCR) operations and ensure broadcasts go out on time",
    "Operate, troubleshoot and maintain broadcast equipment",
    "Ensure broadcast quality and compliance",
    "Handle emergencies and carry out contingency plans to keep transmission running",
])
EQUIPMENT = ("Ross MC1 Switcher, Aveco Astra, Ross XPression, Blackmagic Videohub, "
             "Ross DashBoard, vMix, OBS, Magicsoft CG, AJA Ingest")

EXPERIENCE = [
    dict(company="Channel One News", position="MCR Executive", start_date="2025-12", end_date="",
         is_current=True, location="Dhaka, Bangladesh",
         description="Master Control Room operations for a television news channel.",
         responsibilities=RESPONSIBILITIES, achievements="", technologies=EQUIPMENT, sort_order=0),
    dict(company="Asian Telecast Ltd.", position="MCR Executive", start_date="2022-10", end_date="2026-01",
         is_current=False, location="Dhaka, Bangladesh",
         description="Master Control Room operations and live broadcast transmission.",
         responsibilities=RESPONSIBILITIES,
         achievements=("Emergency response excellence: managed critical situations during unforeseen "
                       "technical failures, minimising broadcast disruption and keeping transmission "
                       "continuous"),
         technologies=EQUIPMENT, sort_order=1),
]

EDUCATION = [
    dict(institution="Eastern University", degree="Bachelor of Science in Computer Science",
         field="Computer Science & Engineering (CSE)", start_date="2022", end_date="", is_current=True,
         description="Session 2022-23.", sort_order=0),
    dict(institution="Khilgaon Model University College", degree="Higher Secondary Certificate (HSC)",
         field="Science", start_date="2019", end_date="2021", is_current=False,
         description="GPA 4.67 out of 5, Dhaka Board.", sort_order=1),
    dict(institution="Pashchim Tafal Baria Secondary School", degree="Secondary School Certificate (SSC)",
         field="Science", start_date="2019", end_date="2019", is_current=False,
         description="GPA 3.72 out of 5, Barisal Board.", sort_order=2),
]

# (period, title, kind, description, title of an older seeded draft to replace)
TIMELINE = [
    ("2019", "Secondary School Certificate (Science)", "education",
     "Pashchim Tafal Baria Secondary School, Barisal Board.", None),
    ("2021", "Higher Secondary Certificate (Science)", "education",
     "Khilgaon Model University College, Dhaka Board. GPA 4.67.", None),
    ("Oct 2022", "Joined Asian Telecast Ltd. as MCR Executive", "broadcast",
     "Started working in the Master Control Room, operating live broadcast transmission.",
     "Joined broadcast operations"),
    ("2022-23", "Began B.Sc. in Computer Science at Eastern University", "education",
     "Department of Computer Science & Engineering.",
     "Began B.Sc. in Computer Science & Engineering"),
    ("2023", "Started writing code", "development",
     "Began learning Python, HTML, CSS and JavaScript and built my first website.", None),
    ("Mar-May 2025", "Completed Python (Django) training at IIT, Jahangirnagar University", "development",
     "80-hour EDGE project training by Bangladesh Computer Council, ICT Division.", None),
    ("Dec 2025", "Joined Channel One News as MCR Executive", "broadcast",
     "Master Control Room operations for a television news channel.", None),
]

# (name, category, icon, description, proficiency, visible-if-new)
SKILLS = [
    ("Python", "Programming", "si:python", "Scripting, automation and back-end development.", "Advanced", True),
    ("Java", "Programming", "si:openjdk", "Object-oriented programming.", "Intermediate", True),
    ("C", "Programming", "si:c", "Systems and procedural programming.", "Proficient", True),
    ("MCR Operations", "Broadcast Technology", "broadcast",
     "24/7 Master Control Room operations and live transmission.", "", True),
    ("Ross MC1 Switcher", "Broadcast Technology", "monitor", "Master control switching.", "", True),
    ("Aveco Astra", "Broadcast Technology", "playout", "Broadcast automation and playout.", "", True),
    ("Ross XPression", "Broadcast Technology", "layers", "Real-time character generator (CG) graphics.", "", True),
    ("Blackmagic Videohub", "Broadcast Technology", "si:blackmagicdesign", "Video routing.", "", True),
    ("Ross DashBoard", "Broadcast Technology", "dashboard", "Broadcast equipment control and monitoring.", "", True),
    ("vMix", "Broadcast Technology", "playout", "Live video production and streaming.", "", True),
    ("OBS", "Broadcast Technology", "si:obsstudio", "Streaming and recording.", "", True),
    ("Magicsoft CG", "Broadcast Technology", "layers", "On-air character generator graphics.", "", True),
    ("AJA Ingest", "Broadcast Technology", "download", "Video ingest and capture.", "", True),
    ("Broadcast Signal Monitoring", "Broadcast Technology", "signal",
     "Broadcast quality and compliance monitoring.", "", True),
    ("Adobe Premiere Pro", "Video Editing", "playout", "Video editing.", "", True),
    ("EDIUS", "Video Editing", "playout", "Broadcast video editing.", "", True),
    ("Filmora", "Video Editing", "playout", "Video editing.", "", True),
    ("Linux", "Operating Systems", "si:linux", "", "", True),
    ("Windows", "Operating Systems", "monitor", "", "", True),
    ("macOS", "Operating Systems", "si:apple", "", "", True),
    # Office tools are on the CV but hidden by default to keep the arsenal focused.
    ("MS Word", "Productivity", "file", "", "", False),
    ("MS Excel", "Productivity", "file", "", "", False),
    ("MS PowerPoint", "Productivity", "file", "", "", False),
    ("Google Docs", "Productivity", "file", "", "", False),
    ("WPS Office", "Productivity", "file", "", "", False),
    ("Canva", "Productivity", "palette", "", "", False),
]
SKILL_RENAMES = {"Ross Production Systems": "Ross MC1 Switcher"}
CATEGORY_ORDER = ["Programming", "Web Development", "Broadcast Technology", "Video Editing",
                  "Cybersecurity", "Operating Systems", "Tools", "Productivity"]

PORTFOLIO_PROJECT = dict(
    title="Personal Portfolio", slug="personal-portfolio",
    tagline="This site: an animated portfolio with a secure admin CMS",
    summary=("My personal portfolio, rebuilt from a simple Python web project into an animated "
             "site with a private control center for managing every piece of content and design."),
    description=("This portfolio started as a small Python web project (during my Python (Django) "
                 "training at IIT, Jahangirnagar University) with a few HTML pages and a contact form.\n\n"
                 "It has since been rebuilt with Flask and SQLAlchemy into a full content-managed site: "
                 "an animated public portfolio plus a secure admin dashboard with authentication, "
                 "image uploads, drag-and-drop ordering and a design center with live preview."),
    highlights="\n".join([
        "Secure admin login with hashed passwords, CSRF protection and rate limiting",
        "Content management for projects, skills, experience and education",
        "Design center with live preview and a draft/publish workflow",
        "Animated, responsive and accessible public site",
    ]),
    tech_stack="Python, Flask, SQLAlchemy, HTML, CSS, JavaScript",
    github_url=f"https://github.com/{GITHUB}/my_portfolio",
    status="maintained", featured=True, visible=True,
)

# Projects from public GitHub repositories (described from each repo's README and code).
GITHUB_PROJECTS = [
    PORTFOLIO_PROJECT,
    dict(
        title="Tea Shop (Cha Bazaar)", slug="tea-shop",
        tagline="A responsive e-commerce storefront for tea",
        summary=("A front-end tea shop with a product catalogue, live search and sorting, and a "
                 "shopping cart that remembers its contents between visits."),
        description=("Cha Bazaar is a responsive e-commerce front end for a tea shop, built with HTML, "
                     "Bootstrap and vanilla JavaScript.\n\n"
                     "Visitors can browse teas in a responsive product grid, search and sort the "
                     "catalogue, and manage a slide-out cart with quantity controls. The cart is "
                     "persisted in the browser's localStorage, so it survives page reloads."),
        highlights="\n".join([
            "Product listing in a responsive grid",
            "Search and sort the catalogue",
            "Slide-out cart with quantity controls, clear cart and checkout",
            "Cart persisted with localStorage",
        ]),
        tech_stack="JavaScript, HTML, CSS, Bootstrap",
        github_url=f"https://github.com/{GITHUB}/Tea_shop",
        status="completed", featured=True, visible=True,
    ),
]

# Certificates supplied by the owner (details only - the certificate images are not published).
# Dates marked "from PDF metadata" come from the certificate file's creation date.
CERTIFICATIONS = [
    dict(kind="certification", name="Python (Django) Training",
         issuer="Institute of Information Technology (IIT), Jahangirnagar University", date="2025-06",
         description=("80-hour training on Python and Django (Mar-May 2025) under the Enhancing Digital "
                      "Government and Economy (EDGE) project of Bangladesh Computer Council, ICT Division.")),
    dict(kind="certification", name="Cyber Hygiene Training",
         issuer="The Asia Foundation & SAJIDA Foundation", date="2025-07",
         description=("Completed cyber hygiene training under the APAC Cybersecurity Fund, "
                      "with support from Google.org.")),
    dict(kind="certification", name="e-Awareness Olympiad: Cyber Safety",
         issuer="ICT Division, Government of Bangladesh & Dnet", date="2020-04",  # from PDF metadata
         description=("Completed 20 rounds of quizzes on cyber safety and preventing violent extremism "
                      "under USAID's Obirodh: Road to Tolerance programme.")),
    dict(kind="course", name="Linking with LinkedIn",
         issuer="Smartifier Academy & SILSWA", date="2020-08",
         description="Online session on using LinkedIn effectively for professional networking."),
    dict(kind="course", name="Training on How to Earn from Social Media Marketing",
         issuer="Volunteer Opportunities", date="",
         description="Training session on social media marketing."),
    dict(kind="award", name="Cycle Rally for Lead-Free Bangladesh",
         issuer="Volunteer for Bangladesh (JAAGO Foundation) & Pure Earth Bangladesh", date="2025-10",
         description="Took part in the awareness cycle rally for a lead-free Bangladesh on 31 October 2025."),
    dict(kind="award", name="Akij Bicycle Purbachal Cycling Challenge 2025",
         issuer="Purbachal Cycling Challenge", date="2025",
         description="ITT-MTB category: ranked 81st of 136 riders, chip time 00:52:24."),
    dict(kind="award", name="Akij Bicycle Cumilla MTB Challenge 2024",
         issuer="Triathlon Dreamers & Team Kotbari", date="2024-10",
         description="Finished 66th of 150 in the male category with a time of 01:30:26."),
    dict(kind="award", name="Family Cyclist Virtual Challenge 2024",
         issuer="Family Cyclists", date="2024-05",
         description="Completed the 30 km category (20-25 May 2024)."),
    dict(kind="award", name="BDCyclists & Friends Independence Day Challenge",
         issuer="BDCyclists", date="2023-03",
         description="Completed the Independence Day cycling challenge on 26 March 2023."),
    dict(kind="award", name="Virtual Cycling Challenge 2022",
         issuer="Pedal Gang", date="2022-08",
         description="Completed the three-day challenge (11-13 August 2022)."),
    dict(kind="award", name="Hemonto 200 km Virtual Cycling Challenge",
         issuer="Hemonto Riders", date="2021-08",  # from PDF metadata
         description="Finisher: completed 200 km of cycling."),
]


def sync_certifications(commit: bool = True) -> list[str]:
    """Create any missing certificates/awards (existing entries are never overwritten)."""
    log = []
    # newest first within each group; undated entries last
    certs = sorted([c for c in CERTIFICATIONS if c["kind"] != "award"], key=lambda c: c["date"] or "0", reverse=True)
    awards = sorted([c for c in CERTIFICATIONS if c["kind"] == "award"], key=lambda c: c["date"] or "0", reverse=True)
    for i, data in enumerate(certs + awards):
        if Certification.query.filter_by(name=data["name"]).first():
            log.append(f"kept: {data['name']}")
            continue
        db.session.add(Certification(sort_order=i, visible=True, **data))
        log.append(f"created: {data['name']}")
    if commit:
        db.session.commit()
    return log


SOCIALS = [
    dict(platform="github", label="GitHub", handle=f"@{GITHUB}", url=f"https://github.com/{GITHUB}"),
    dict(platform="email", label="Email", handle=EMAIL, url=f"mailto:{EMAIL}"),
]


def _upsert(model, lookup: dict, data: dict, fallback=None):
    row = model.query.filter_by(**lookup).first() or fallback
    created = row is None
    if created:
        row = model()
        db.session.add(row)
    for k, v in data.items():
        setattr(row, k, v)
    return row, created


def sync_cv_content() -> list[str]:
    """Apply the CV facts to the database. Returns a list of changes."""
    log: list[str] = []

    prof = Profile.get()
    prof.rotating_titles = TITLES
    prof.short_intro = INTRO
    prof.about = ABOUT
    prof.email = EMAIL
    prof.location = "Dhaka, Bangladesh"
    prof.github_username = GITHUB
    prof.seo_description = ("Portfolio of Sanjidur Rahman Sanjid: MCR Executive with three years of "
                            "broadcast operations experience, software developer and CSE student.")
    log.append("updated profile")

    # Experience / education: reuse the seeded "(edit me)" drafts instead of leaving them behind.
    xp_draft = Experience.query.filter(Experience.company.like("%(edit me)%")).first()
    for data in reversed(EXPERIENCE):  # oldest first, so the draft becomes Asian Telecast
        row, created = _upsert(Experience, {"company": data["company"]}, data, xp_draft)
        if row is xp_draft:
            xp_draft = None
        row.visible = True
        log.append(("created" if created else "updated") + f" experience: {data['company']}")

    edu_draft = Education.query.filter(Education.institution.like("%(edit me)%")).first()
    for data in EDUCATION:
        fb = edu_draft if data["institution"] == "Eastern University" else None
        row, created = _upsert(Education, {"institution": data["institution"]}, data, fb)
        row.visible = True
        log.append(("created" if created else "updated") + f" education: {data['institution']}")

    # Timeline in chronological order; untouched drafts (security, CyberQuest) go last.
    ordered = []
    for period, title, kind, desc, old_title in TIMELINE:
        fb = TimelineEvent.query.filter_by(title=old_title).first() if old_title else None
        row, created = _upsert(TimelineEvent, {"title": title},
                               dict(period=period, title=title, kind=kind, description=desc, visible=True), fb)
        ordered.append(row)
        if created:
            log.append(f"created milestone: {title}")
    db.session.flush()
    for i, e in enumerate(ordered + [e for e in TimelineEvent.ordered().all() if e not in ordered]):
        e.sort_order = i

    # Skills
    for old, new in SKILL_RENAMES.items():
        s = Skill.query.filter_by(name=old).first()
        if s and not Skill.query.filter_by(name=new).first():
            s.name = new
            log.append(f"renamed skill: {old} -> {new}")
    for name, cat, icon, desc, level, visible in SKILLS:
        s = Skill.query.filter_by(name=name).first()
        if s is None:
            s = Skill(name=name, visible=visible, sort_order=10_000)
            db.session.add(s)
            log.append(f"created skill: {name}" + ("" if visible else " (hidden)"))
        s.category, s.icon = cat, icon
        if desc:
            s.description = desc
        if level:
            s.proficiency = level
    db.session.flush()
    skills = Skill.ordered().all()
    skills.sort(key=lambda s: (CATEGORY_ORDER.index(s.category) if s.category in CATEGORY_ORDER else 99,
                               s.sort_order))
    for i, s in enumerate(skills):
        s.sort_order = i

    log.extend(sync_projects(commit=False))
    log.extend(sync_certifications(commit=False))

    for i, data in enumerate(SOCIALS):
        row, created = _upsert(SocialLink, {"platform": data["platform"]}, data)
        if created:
            row.sort_order, row.visible = i, True
            log.append(f"created social link: {data['platform']}")

    db.session.commit()
    return log


def sync_projects(commit: bool = True) -> list[str]:
    """Add/update the GitHub-based projects only (does not touch profile or other content)."""
    log = []
    for data in GITHUB_PROJECTS:
        row = Project.query.filter_by(slug=data["slug"]).first()
        created = row is None
        if created:
            row = Project(sort_order=(db.session.query(db.func.max(Project.sort_order)).scalar() or 0) + 1)
            db.session.add(row)
            for k, v in data.items():
                setattr(row, k, v)
        log.append(("created" if created else "kept") + f" project: {data['title']}")
    if commit:
        db.session.commit()
    return log
