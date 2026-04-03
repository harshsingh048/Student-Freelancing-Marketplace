"""
tests/test_api.py
──────────────────
Integration tests using FastAPI's TestClient (sync) and httpx (async-compatible).
These tests use an in-memory SQLite database to avoid needing a real Postgres instance.

Run:
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

# ── Override settings BEFORE importing the app ───────────────────────────────
import os
os.environ["DATABASE_URL"]    = "sqlite+aiosqlite:///./test.db"
os.environ["SECRET_KEY"]      = "test-secret-key-12345"
os.environ["ADMIN_EMAIL"]     = "admin@test.com"
os.environ["ADMIN_PASSWORD"]  = "AdminPass@1"

from app.main import app  # noqa: E402

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
#  Fixtures
# ─────────────────────────────────────────────────────────────────────────────

STUDENT_DATA = {
    "full_name": "Alice Dev",
    "email": "alice@example.com",
    "password": "SecurePass1",
    "skills": ["Python", "FastAPI"],
    "bio": "Full-stack student developer",
}

CLIENT_DATA = {
    "full_name": "Bob Buyer",
    "email": "bob@example.com",
    "password": "SecurePass1",
}


def signup_student() -> dict:
    r = client.post("/api/v1/auth/signup/student", json=STUDENT_DATA)
    assert r.status_code == 201, r.text
    return r.json()["data"]


def signup_client() -> dict:
    r = client.post("/api/v1/auth/signup/client", json=CLIENT_DATA)
    assert r.status_code == 201, r.text
    return r.json()["data"]


def auth_header(token_response: dict) -> dict:
    return {"Authorization": f"Bearer {token_response['access_token']}"}


# ─────────────────────────────────────────────────────────────────────────────
#  Auth tests
# ─────────────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_student_signup():
    data = signup_student()
    assert data["user"]["role"] == "student"
    assert data["user"]["email"] == STUDENT_DATA["email"]


def test_duplicate_signup():
    r = client.post("/api/v1/auth/signup/student", json=STUDENT_DATA)
    assert r.status_code == 409


def test_client_signup():
    data = signup_client()
    assert data["user"]["role"] == "client"


def test_login():
    r = client.post("/api/v1/auth/login", json={
        "email": STUDENT_DATA["email"],
        "password": STUDENT_DATA["password"],
    })
    assert r.status_code == 200
    assert "access_token" in r.json()["data"]


def test_login_wrong_password():
    r = client.post("/api/v1/auth/login", json={
        "email": STUDENT_DATA["email"],
        "password": "WrongPass999",
    })
    assert r.status_code == 401


def test_me_endpoint():
    tokens = signup_student() if False else client.post(
        "/api/v1/auth/login",
        json={"email": STUDENT_DATA["email"], "password": STUDENT_DATA["password"]},
    ).json()["data"]
    r = client.get("/api/v1/auth/me", headers=auth_header(tokens))
    assert r.status_code == 200
    assert r.json()["data"]["email"] == STUDENT_DATA["email"]


# ─────────────────────────────────────────────────────────────────────────────
#  Gig tests
# ─────────────────────────────────────────────────────────────────────────────

GIG_DATA = {
    "title": "I will build a FastAPI backend for you",
    "description": "Professional REST API using FastAPI, SQLAlchemy and PostgreSQL with full auth.",
    "category": "web_development",
    "price": 2500.00,
    "delivery_days": 5,
    "revision_count": 2,
}


def _student_tokens():
    return client.post(
        "/api/v1/auth/login",
        json={"email": STUDENT_DATA["email"], "password": STUDENT_DATA["password"]},
    ).json()["data"]


def _client_tokens():
    return client.post(
        "/api/v1/auth/login",
        json={"email": CLIENT_DATA["email"], "password": CLIENT_DATA["password"]},
    ).json()["data"]


def test_create_gig():
    tokens = _student_tokens()
    r = client.post("/api/v1/gigs", json=GIG_DATA, headers=auth_header(tokens))
    assert r.status_code == 201
    assert r.json()["data"]["title"] == GIG_DATA["title"]


def test_list_gigs():
    r = client.get("/api/v1/gigs")
    assert r.status_code == 200
    assert "items" in r.json()["data"]


def test_client_cannot_create_gig():
    tokens = _client_tokens()
    r = client.post("/api/v1/gigs", json=GIG_DATA, headers=auth_header(tokens))
    assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
#  Order lifecycle test
# ─────────────────────────────────────────────────────────────────────────────

def test_full_order_lifecycle():
    student_tokens = _student_tokens()
    client_tokens  = _client_tokens()

    # 1. Get a gig ID
    gigs_r = client.get("/api/v1/gigs")
    gig_id = gigs_r.json()["data"]["items"][0]["id"]

    # 2. Client places order
    order_r = client.post(
        "/api/v1/orders",
        json={"gig_id": gig_id, "requirements": "Please build an e-commerce API with cart."},
        headers=auth_header(client_tokens),
    )
    assert order_r.status_code == 201
    order_id   = order_r.json()["data"]["order"]["id"]
    rz_order_id = order_r.json()["data"]["payment_details"]["razorpay_order_id"]

    # 3. Verify mock payment
    verify_r = client.post(
        "/api/v1/orders/verify-payment",
        json={
            "order_id":            order_id,
            "razorpay_order_id":   rz_order_id,
            "razorpay_payment_id": "pay_mock_abc123",
            "razorpay_signature":  "mock_sig",
        },
        headers=auth_header(client_tokens),
    )
    assert verify_r.status_code == 200

    # 4. Student delivers
    deliver_r = client.post(
        f"/api/v1/orders/{order_id}/deliver",
        json={"delivery_note": "Here is the completed FastAPI backend with all endpoints."},
        headers=auth_header(student_tokens),
    )
    assert deliver_r.status_code == 200

    # 5. Client approves
    approve_r = client.post(
        f"/api/v1/orders/{order_id}/approve",
        headers=auth_header(client_tokens),
    )
    assert approve_r.status_code == 200

    # 6. Client submits review
    review_r = client.post(
        "/api/v1/reviews",
        json={"order_id": order_id, "rating": 5, "comment": "Excellent work, very professional!"},
        headers=auth_header(client_tokens),
    )
    assert review_r.status_code == 201
    assert review_r.json()["data"]["rating"] == 5
