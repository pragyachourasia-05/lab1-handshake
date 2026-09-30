"""Run from backend/:  pytest -q   (uses a throwaway SQLite DB, not MySQL)."""
import os
import tempfile

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import pytest
from fastapi.testclient import TestClient

from app.main import app

SIGNUP = {
    "name": "Pragya",
    "email": "Pragya@Example.com",
    "password": "Secret123",
    "college_name": "San Jose State University",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_signup_login_profile_flow(client):
    r = client.post("/students/signup", json=SIGNUP)
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "pragya@example.com"  # normalized

    assert client.post("/students/signup", json=SIGNUP).status_code == 409

    bad = client.post("/students/login", json={"email": SIGNUP["email"], "password": "wrong"})
    assert bad.status_code == 401

    r = client.post("/students/login", json={"email": SIGNUP["email"], "password": "Secret123"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    me = client.get("/students/me", headers=auth(token))
    assert me.status_code == 200 and me.json()["college_name"] == SIGNUP["college_name"]

    upd = client.put(
        "/students/me",
        headers=auth(token),
        json={"city": "San Jose", "major": "Data Science", "cgpa": 3.8,
              "graduation_year": 2027, "skills": ["Python", "SQL", "python"]},
    )
    assert upd.status_code == 200
    assert upd.json()["skills"] == ["Python", "SQL"]
    assert upd.json()["name"] == "Pragya"  # untouched fields preserved


def test_validation(client):
    weak = {**SIGNUP, "email": "a@b.com", "password": "short"}
    assert client.post("/students/signup", json=weak).status_code == 422
    nodigit = {**SIGNUP, "email": "a@b.com", "password": "abcdefgh"}
    assert client.post("/students/signup", json=nodigit).status_code == 422
    token = client.post("/students/login", json={"email": SIGNUP["email"], "password": "Secret123"}).json()["access_token"]
    for body in ({"cgpa": 5.0}, {"phone": "abc"}, {"date_of_birth": "2999-01-01"}, {"name": None}):
        assert client.put("/students/me", headers=auth(token), json=body).status_code == 422


def test_logout_revokes_token(client):
    token = client.post("/students/login", json={"email": SIGNUP["email"], "password": "Secret123"}).json()["access_token"]
    assert client.post("/students/logout", headers=auth(token)).status_code == 200
    assert client.get("/students/me", headers=auth(token)).status_code == 401


def test_unauthenticated_and_bad_token(client):
    assert client.get("/students/me").status_code == 401
    assert client.get("/students/me", headers=auth("garbage")).status_code == 401


def test_preferences_and_browse(client):
    token = client.post("/students/login", json={"email": SIGNUP["email"], "password": "Secret123"}).json()["access_token"]
    assert client.get("/students/me/preferences", headers=auth(token)).json()["saved"] is False
    r = client.put("/students/me/preferences", headers=auth(token),
                   json={"preferred_categories": ["internship"], "preferred_cities": ["San Jose"], "remote_ok": True})
    assert r.status_code == 200 and r.json()["saved"] is True
    assert client.put("/students/me/preferences", headers=auth(token),
                      json={"preferred_categories": ["bogus"]}).status_code == 422

    rows = client.get("/students?major=data", headers=auth(token)).json()
    assert len(rows) == 1 and rows[0]["name"] == "Pragya"
    assert "email" not in rows[0]
    assert client.get("/students/999", headers=auth(token)).status_code == 404


def test_profile_picture(client):
    token = client.post("/students/login", json={"email": SIGNUP["email"], "password": "Secret123"}).json()["access_token"]
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 50
    r = client.post("/students/me/profile-picture", headers=auth(token), files={"file": ("a.png", png, "image/png")})
    assert r.status_code == 200
    url = r.json()["profile_picture_url"]
    assert client.get(url).status_code == 200
    fake = client.post("/students/me/profile-picture", headers=auth(token), files={"file": ("a.png", b"notanimage", "image/png")})
    assert fake.status_code == 400
    pdf = client.post("/students/me/profile-picture", headers=auth(token), files={"file": ("a.pdf", b"%PDF", "application/pdf")})
    assert pdf.status_code == 415
