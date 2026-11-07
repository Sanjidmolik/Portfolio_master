import io
import re
import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from portfolio import create_app
from portfolio.extensions import db, limiter
from portfolio.models import AdminUser

PASSWORD = "Sup3r-Secret-Pass"


@pytest.fixture()
def app():
    tmp = Path(tempfile.mkdtemp())
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp / 'test.db'}",
        "UPLOAD_FOLDER": tmp / "static" / "uploads",
        "RATELIMIT_ENABLED": True,
        "GITHUB_CACHE_SECONDS": 3600,
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
        from portfolio.seed import seed_if_empty
        seed_if_empty()
        u = AdminUser(username="admin")
        u.set_password(PASSWORD)
        db.session.add(u)
        db.session.commit()
    limiter.reset()
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_from(html: bytes) -> str:
    m = re.search(rb'name="csrf_token" value="([^"]+)"', html) or re.search(rb'name="csrf-token" content="([^"]+)"', html)
    assert m, "csrf token not found"
    return m.group(1).decode()


@pytest.fixture()
def login(client):
    def _login(username="admin", password=PASSWORD):
        token = csrf_from(client.get("/admin/login").data)
        return client.post("/admin/login", data={"username": username, "password": password, "csrf_token": token})
    return _login


@pytest.fixture()
def admin_client(client, login):
    r = login()
    assert r.status_code == 302
    return client


def admin_token(client, path="/admin/"):
    return csrf_from(client.get(path).data)


def png_bytes(size=(64, 48), color=(30, 120, 220)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    buf.seek(0)
    return buf
