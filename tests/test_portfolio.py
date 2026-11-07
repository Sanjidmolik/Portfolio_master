import io
import json

from portfolio import design
from portfolio.extensions import db
from portfolio.models import Message, Profile, Project, Skill

from .conftest import PASSWORD, admin_token, csrf_from, png_bytes


# ------------------------------------------------------------------ public
def test_public_pages_render(client):
    for url in ["/", "/projects", "/projects/cyberquest", "/robots.txt", "/sitemap.xml", "/og-image.png"]:
        assert client.get(url).status_code == 200, url
    home = client.get("/").data.decode()
    assert "Sanjidur Rahman Sanjid" in home
    assert "CyberQuest" in home
    assert "Content-Security-Policy" in client.get("/").headers


def test_legacy_routes_redirect(client):
    assert client.get("/about").status_code == 301
    assert client.get("/contact").status_code == 301


def test_hidden_seed_content_not_public(client):
    html = client.get("/").data.decode()
    # unconfirmed starter skills and office tools stay hidden drafts
    for hidden in ("Digital Forensics", "MS Word", "(edit me)"):
        assert hidden not in html, hidden


def test_cv_content_published_without_private_details(client):
    html = client.get("/").data.decode()
    for shown in ("Channel One News", "Asian Telecast Ltd.", "Eastern University", "MCR Executive",
                  "Ross MC1 Switcher", "sanjid.molik123@gmail.com", "Personal Portfolio"):
        assert shown in html, shown
    # Private CV details must never be published. They are checked by pattern / hash so that
    # this test file itself does not contain them (it is committed to a public repository).
    import hashlib
    import re
    assert not re.search(r"(?:\+?880|\b0)1[3-9]\d{8}\b", html), "a Bangladeshi phone number is published"
    private_word_hashes = {"ac5e54b28b9c83b1", "bd1c178ec1daa7f1", "fe353605af2ea534", "19418dc845ad9fb6",
                           "2036c509b480078f", "eb30844cdfbc2f00", "8656ec06f2cb5b64"}
    words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", html)}
    leaked = {w for w in words if hashlib.sha256(w.encode()).hexdigest()[:16] in private_word_hashes}
    assert not leaked, "private address/family details are published"


def test_cv_sync_is_idempotent_and_keeps_visibility(app):
    from portfolio.cv_content import sync_cv_content
    from portfolio.models import Education, Experience
    with app.app_context():
        Skill.query.filter_by(name="Linux").first().visible = False
        db.session.commit()
        counts = (Skill.query.count(), Experience.query.count(), Education.query.count())
        sync_cv_content()
        assert (Skill.query.count(), Experience.query.count(), Education.query.count()) == counts
        assert Skill.query.filter_by(name="Linux").first().visible is False


def test_unpublished_project_404_for_public(app, client):
    with app.app_context():
        Project.query.filter_by(slug="cyberquest").first().visible = False
        db.session.commit()
    assert client.get("/projects/cyberquest").status_code == 404


def test_sitemap_and_robots(client):
    assert b"/projects/cyberquest" in client.get("/sitemap.xml").data
    assert b"Disallow: /admin" in client.get("/robots.txt").data


# ------------------------------------------------------------------ contact
def _contact(client, **data):
    token = csrf_from(client.get("/").data)
    payload = {"name": "Ada Lovelace", "email": "ada@example.com", "subject": "Hi", "message": "Hello there, nice site!",
               "csrf_token": token}
    payload.update(data)
    return client.post("/contact", data=payload, headers={"Accept": "application/json"})


def test_contact_form_saves_message(app, client):
    r = _contact(client)
    assert r.status_code == 200 and r.json["ok"]
    with app.app_context():
        assert Message.query.count() == 1


def test_contact_validation(client):
    r = _contact(client, email="not-an-email", message="short")
    assert r.status_code == 422
    assert set(r.json["fields"]) == {"email", "message"}


def test_contact_requires_csrf(client):
    r = client.post("/contact", data={"name": "x", "email": "a@b.co", "message": "1234567890"},
                    headers={"Accept": "application/json"})
    assert r.status_code == 400


def test_contact_honeypot(app, client):
    r = _contact(client, website="http://spam")
    assert r.json["ok"]
    with app.app_context():
        assert Message.query.count() == 0


def test_contact_rate_limited(client):
    codes = [_contact(client).status_code for _ in range(7)]
    assert 429 in codes


# ------------------------------------------------------------------ auth
def test_admin_requires_login(client):
    for url in ["/admin/", "/admin/profile", "/admin/r/skills", "/admin/design", "/admin/messages", "/admin/account"]:
        r = client.get(url)
        assert r.status_code == 302 and "/admin/login" in r.headers["Location"], url


def test_admin_api_rejects_anonymous(client):
    r = client.post("/admin/design/publish", json={}, headers={"Accept": "application/json"})
    assert r.status_code in (400, 401)  # CSRF or auth - never allowed
    r = client.post("/admin/r/skills/reorder", json={"ids": [1]}, headers={"Accept": "application/json"})
    assert r.status_code in (400, 401)


def test_login_wrong_password(login):
    r = login(password="wrong")
    assert r.status_code == 401
    assert b"Invalid username or password" in r.data


def test_login_and_logout(client, login):
    assert login().status_code == 302
    assert client.get("/admin/").status_code == 200
    token = admin_token(client)
    client.post("/admin/logout", data={"csrf_token": token})
    assert client.get("/admin/").status_code == 302


def test_login_rate_limit(login):
    codes = [login(password="nope").status_code for _ in range(7)]
    assert codes[-1] == 429


def test_open_redirect_blocked(client):
    token = csrf_from(client.get("/admin/login").data)
    r = client.post("/admin/login?next=https://evil.example", data={"username": "admin", "password": PASSWORD, "csrf_token": token})
    assert r.headers["Location"].endswith("/admin/")


def test_password_change_revokes_other_sessions(app, login, client):
    login()
    other = app.test_client()
    t = csrf_from(other.get("/admin/login").data)
    other.post("/admin/login", data={"username": "admin", "password": PASSWORD, "csrf_token": t})
    assert other.get("/admin/").status_code == 200
    token = admin_token(client, "/admin/account")
    r = client.post("/admin/account", data={"csrf_token": token, "action": "password", "current_password": PASSWORD,
                                            "new_password": "N3w-Password-123", "confirm_password": "N3w-Password-123"})
    assert r.status_code == 302
    assert client.get("/admin/").status_code == 200       # this session kept
    assert other.get("/admin/").status_code == 302        # other session revoked


# ------------------------------------------------------------------ CRUD
def test_create_skill_and_show_publicly(app, admin_client):
    token = admin_token(admin_client, "/admin/r/skills/new")
    r = admin_client.post("/admin/r/skills/new", data={
        "csrf_token": token, "name": "Bash", "category": "Tools", "icon": "terminal",
        "description": "Shell scripting", "proficiency": "", "years": "", "visible": "on"})
    assert r.status_code == 302
    html = admin_client.get("/").data.decode()
    assert "Bash" in html and 'id="skills"' in html


def test_skill_validation(admin_client):
    token = admin_token(admin_client, "/admin/r/skills/new")
    r = admin_client.post("/admin/r/skills/new", data={"csrf_token": token, "name": "", "category": "Tools", "icon": "<script>"})
    assert r.status_code == 422


def test_toggle_reorder_delete(app, admin_client):
    with app.app_context():
        ids = [s.id for s in Skill.ordered().all()]
    token = admin_token(admin_client)
    r = admin_client.post(f"/admin/r/skills/{ids[0]}/toggle", data={"csrf_token": token, "attr": "visible"},
                          headers={"Accept": "application/json"})
    assert r.json["value"] is True
    r = admin_client.post("/admin/r/skills/reorder", json={"ids": list(reversed(ids))},
                          headers={"X-CSRFToken": token, "Accept": "application/json"})
    assert r.json["ok"]
    with app.app_context():
        assert Skill.ordered().first().id == ids[-1]
    r = admin_client.post(f"/admin/r/skills/{ids[0]}/delete", data={"csrf_token": token})
    assert r.status_code == 302
    with app.app_context():
        assert db.session.get(Skill, ids[0]) is None


def test_project_with_upload_and_gallery(app, admin_client):
    token = admin_token(admin_client, "/admin/r/projects/new")
    r = admin_client.post("/admin/r/projects/new", content_type="multipart/form-data", data={
        "csrf_token": token, "title": "Signal Monitor", "slug": "", "status": "completed", "visible": "on",
        "tech_stack": "Python,  Flask ,", "github_url": "https://github.com/x/y", "demo_url": "",
        "thumbnail": (png_bytes(), "shot.png")})
    assert r.status_code == 302
    with app.app_context():
        p = Project.query.filter_by(slug="signal-monitor").first()
        assert p and p.thumbnail.endswith(".webp") and p.tech_stack == "Python, Flask"
        pid = p.id
    r = admin_client.post(f"/admin/projects/{pid}/images", content_type="multipart/form-data",
                          data={"csrf_token": token, "images": [(png_bytes(), "a.png"), (png_bytes(), "b.jpg")]})
    assert r.status_code == 302
    with app.app_context():
        assert len(db.session.get(Project, pid).images) == 2
    assert b"Signal Monitor" in admin_client.get("/projects/signal-monitor").data


def test_rejects_non_image_upload(app, admin_client):
    token = admin_token(admin_client, "/admin/r/projects/new")
    r = admin_client.post("/admin/r/projects/new", content_type="multipart/form-data", data={
        "csrf_token": token, "title": "Evil", "status": "completed",
        "thumbnail": (io.BytesIO(b"<?php system($_GET['x']); ?>"), "evil.png")})
    assert r.status_code == 422
    assert b"not a valid image" in r.data


def test_rejects_javascript_urls(admin_client):
    token = admin_token(admin_client, "/admin/r/projects/new")
    r = admin_client.post("/admin/r/projects/new", data={
        "csrf_token": token, "title": "X", "status": "completed", "github_url": "javascript:alert(1)"})
    assert r.status_code == 422


def test_profile_update(app, admin_client):
    token = admin_token(admin_client, "/admin/profile")
    data = {"csrf_token": token, "full_name": "Sanjidur Rahman Sanjid", "headline": "New headline",
            "short_intro": "Intro text", "email": "hello@example.com", "github_username": "octocat",
            "avatar": (png_bytes((300, 300)), "me.jpg")}
    r = admin_client.post("/admin/profile", data=data, content_type="multipart/form-data")
    assert r.status_code == 302
    with app.app_context():
        prof = Profile.get()
        assert prof.headline == "New headline" and prof.avatar.startswith("uploads/profile/")
    html = admin_client.get("/").data.decode()
    assert "New headline" in html and 'id="github"' in html


def test_resume_must_be_pdf(admin_client):
    token = admin_token(admin_client, "/admin/profile")
    r = admin_client.post("/admin/profile", content_type="multipart/form-data", data={
        "csrf_token": token, "full_name": "A", "headline": "B", "short_intro": "C",
        "resume": (io.BytesIO(b"MZ fake exe"), "cv.pdf")})
    assert r.status_code == 422 and b"not a valid PDF" in r.data


# ------------------------------------------------------------------ design
def test_design_draft_preview_publish(app, admin_client, client):
    token = admin_token(admin_client, "/admin/design")
    d = design.default_design()
    d["colors"]["primary"] = "#ff0000"
    d["sections"][1]["enabled"] = False  # about
    r = admin_client.post("/admin/design/draft", json=d, headers={"X-CSRFToken": token})
    assert r.json["ok"] and r.json["dirty"]
    # Draft is NOT public yet
    assert b"--primary:#ff0000" not in admin_client.get("/").data
    # ...but visible in the admin preview
    assert b"--primary:#ff0000" in admin_client.get("/?preview=draft").data
    # Anonymous users can't use preview mode
    assert b"--primary:#ff0000" not in app.test_client().get("/?preview=draft").data
    r = admin_client.post("/admin/design/publish", json=d, headers={"X-CSRFToken": token})
    assert r.json["ok"]
    html = app.test_client().get("/").data
    assert b"--primary:#ff0000" in html and b'id="about"' not in html


def test_design_sanitizes_input():
    d = design.sanitize({
        "colors": {"primary": "red;}</style><script>", "accent": "#ABCDEF"},
        "typography": {"heading_font": "Comic</style>", "base_size": 999},
        "layout": {"card_style": "x"},
        "sections": [{"key": "evil", "title": "x"}, {"key": "contact", "title": "<b>Hi</b>"}],
    })
    assert d["colors"]["primary"] == "#3b82f6"
    assert d["colors"]["accent"] == "#abcdef"
    assert d["typography"]["heading_font"] == "Space Grotesk"
    assert d["typography"]["base_size"] == 20
    assert d["layout"]["card_style"] == "outline"
    assert d["sections"][0]["key"] == "hero"
    assert {s["key"] for s in d["sections"]} == set(design.SECTION_KEYS)
    css = design.css_variables(d)
    assert "<" not in css and "script" not in css


def test_design_reset_and_compile(admin_client):
    token = admin_token(admin_client, "/admin/design")
    r = admin_client.post("/admin/design/compile", json={"layout": {"radius": 4}}, headers={"X-CSRFToken": token})
    assert "--radius:4px" in r.json["css"]
    r = admin_client.post("/admin/design/reset", json={}, headers={"X-CSRFToken": token})
    assert r.json["design"] == design.default_design()


def test_admin_pages_render(admin_client):
    for url in ["/admin/", "/admin/profile", "/admin/messages", "/admin/design", "/admin/account",
                "/admin/r/skills", "/admin/r/projects", "/admin/r/experience", "/admin/r/timeline",
                "/admin/r/education", "/admin/r/certifications", "/admin/r/socials", "/admin/content",
                "/admin/r/skills/new", "/admin/r/projects/1/edit", "/admin/r/experience/1/edit"]:
        r = admin_client.get(url)
        assert r.status_code == 200, url
        assert r.headers["Cache-Control"] == "no-store"


def test_github_fragment_graceful_without_network(app, admin_client, monkeypatch):
    import portfolio.github as gh
    def boom(*a, **k):
        raise gh.requests.ConnectionError("offline")
    monkeypatch.setattr(gh.requests, "get", boom)
    with app.app_context():
        Profile.get().github_username = "octocat"
        db.session.commit()
    r = admin_client.get("/fragments/github")
    assert r.status_code == 200 and b"temporarily unavailable" in r.data


def test_github_data_rendered_from_cache(app, client):
    from portfolio.models import Setting
    import time
    with app.app_context():
        Profile.get().github_username = "octocat"
        db.session.commit()
        Setting.write("github_cache:octocat", {"ts": time.time(), "data": {
            "profile": {"login": "octocat", "name": "Octo", "avatar": None, "url": "https://github.com/octocat",
                        "bio": "", "public_repos": 8, "followers": 3, "following": 0},
            "stats": {"stars": 5, "forks": 1, "repos": 8}, "languages": [{"name": "Python", "count": 3}],
            "repos": [{"name": "hello", "url": "https://github.com/octocat/hello", "description": "d", "language": "Python",
                       "stars": 5, "forks": 1, "pushed_at": "2026-01-01"}],
            "contributions": None, "fetched_at": "2026-11-07T00:00:00+00:00"}})
    html = client.get("/fragments/github").data.decode()
    assert "octocat/hello" in html and "Python" in html


def test_message_actions(app, admin_client, client):
    assert _contact(client).json["ok"]
    with app.app_context():
        mid = Message.query.first().id
    token = admin_token(admin_client, "/admin/messages")
    admin_client.post(f"/admin/messages/{mid}", data={"csrf_token": token, "action": "read"})
    with app.app_context():
        assert db.session.get(Message, mid).is_read
    admin_client.post(f"/admin/messages/{mid}", data={"csrf_token": token, "action": "delete"})
    with app.app_context():
        assert Message.query.count() == 0


def test_xss_escaped_in_public_output(app, client):
    with app.app_context():
        p = Project.query.first()
        p.title = '<script>alert(1)</script>'
        db.session.commit()
    html = client.get("/").data.decode()
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html


def test_access_pass_and_avatar_style(app, admin_client, client):
    html = client.get("/").data.decode()
    assert "BROADCAST ACCESS PASS" in html and "Channel One News" in html
    assert "avatar-illustrated" in html and 'class="avatar-art"' in html
    token = admin_token(admin_client, "/admin/design")
    d = design.default_design()
    d["identity"]["avatar_style"] = "photo"
    assert admin_client.post("/admin/design/publish", json=d, headers={"X-CSRFToken": token}).json["ok"]
    assert "avatar-photo" in client.get("/").data.decode()
    assert design.sanitize({"identity": {"avatar_style": "<x>"}})["identity"]["avatar_style"] == "illustrated"


def test_site_content_requires_login(client):
    assert client.get("/admin/content").status_code == 302
    assert client.post("/admin/content", data={"hero_greeting": "x"}).status_code in (302, 400)


def test_site_content_edit_updates_public_site(admin_client, client):
    from portfolio import site_content as sc
    token = admin_token(admin_client, "/admin/content")
    data = dict(sc.defaults(), csrf_token=token, hero_greeting="Assalamu alaikum, I'm",
                hero_stat2_title="", focus1_title="Live Broadcast", nav_cta="Hire me")
    r = admin_client.post("/admin/content", data=data)
    assert r.status_code == 302
    html = client.get("/").data.decode()
    assert "Assalamu alaikum, I&#39;m" in html and "Live Broadcast" in html and "Hire me" in html
    assert "<strong>Passionate</strong>" not in html  # empty highlight title hides it


def test_site_content_validation(admin_client):
    from portfolio import site_content as sc
    token = admin_token(admin_client, "/admin/content")
    data = dict(sc.defaults(), csrf_token=token, hero_greeting="", nav_cta="x" * 200,
                focus1_icon="<script>", evil_key="hack")
    r = admin_client.post("/admin/content", data=data)
    assert r.status_code == 422
    body = r.data.decode()
    assert "Greeting is required" in body and "must be 16 characters or fewer" in body
    assert "Choose a built-in icon" in body
    values, errors = sc.validate(data)
    assert "evil_key" not in values and set(errors) == {"hero_greeting", "nav_cta", "focus1_icon"}


def test_profile_errors_keep_typed_values(admin_client):
    token = admin_token(admin_client, "/admin/profile")
    r = admin_client.post("/admin/profile", data={"csrf_token": token, "full_name": "", "headline": "Typed headline",
                                                  "short_intro": "Typed intro", "email": "bad"})
    assert r.status_code == 422
    body = r.data.decode()
    assert "Typed headline" in body and "Full name is required" in body and "valid email" in body


def test_hero_v2_renders_portrait_and_current_card(client):
    html = client.get("/").data.decode()
    assert 'class="hero hv"' in html and "hv-meter" in html
    assert "Currently at" in html and "Channel One News" in html
    assert "Broadcast Operations Professional" in html and "3+ Years" in html


def test_theme_presets_are_valid():
    presets = design.preset_designs()
    assert [p["key"] for p in presets] == design.PRESET_KEYS
    assert set(design.PRESET_KEYS) == set(design.CHOICES["theme.skin"])
    for p in presets:
        assert p["design"] == design.sanitize(p["design"])  # every preset passes validation
        assert p["design"]["theme"]["skin"] == p["key"]
    assert design.sanitize({"theme": {"skin": "<x>"}})["theme"]["skin"] == "broadcast"


def test_theme_presets_apply_and_publish(app, admin_client, client):
    token = admin_token(admin_client, "/admin/design")
    page = admin_client.get("/admin/design").data.decode()
    assert "Neon Hacker" in page and "Professional CEO" in page and "data-apply-preset" in page
    neon = next(p for p in design.preset_designs() if p["key"] == "neon")["design"]
    assert admin_client.post("/admin/design/publish", json=neon, headers={"X-CSRFToken": token}).json["ok"]
    html = client.get("/").data.decode()
    assert "skin-neon" in html and "Orbitron" in html and "--primary:#00e08a" in html


def test_login_page_full_screen(client):
    html = client.get("/admin/login").data.decode()
    assert 'class="auth"' in html and "Welcome back" in html and 'type="password"' in html


def test_certificates_grid_and_filters(client):
    html = client.get("/").data.decode()
    assert 'class="cert-grid"' in html and 'data-cert-filter="award"' in html
    assert html.count('class="cert-card') >= 9


def test_about_paragraphs_handle_windows_line_endings(app, client):
    from portfolio.models import split_paragraphs
    assert split_paragraphs("One.\r\n\r\nTwo.\n\nThree.") == ["One.", "Two.", "Three."]
    with app.app_context():
        prof = Profile.get()
        prof.about = "Short *lead*.\r\n\r\nBody paragraph one.\r\n\r\nBody two."
        db.session.commit()
    html = client.get("/").data.decode()
    assert html.count("class=\"ab-lead\"") == 1 and "Body paragraph one." in html
