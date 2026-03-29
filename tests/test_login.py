import pytest
from app import get_db

def test_login_get_unauthenticated(client):
    """Ensure GET /login returns a 200 OK status."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign In" in response.data

def test_login_authenticated_user_redirects(auth_client):
    """Ensure both GET and POST /login requests by an already logged-in user redirect to /"""
    response_get = auth_client.get("/login")
    assert response_get.status_code == 302
    assert response_get.headers["Location"] == "/"

    response_post = auth_client.post("/login", data={
        "email": "some@email.com",
        "password": "somepassword"
    })
    assert response_post.status_code == 302
    assert response_post.headers["Location"] == "/"

def test_login_post_invalid_credentials(client):
    """Ensure POST /login with an unknown email or incorrect password renders the login page with an error."""
    # Unknown email
    response = client.post("/login", data={
        "email": "unknown@domain.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data

    # Known email, incorrect password
    response2 = client.post("/login", data={
        "email": "admin@meatheadlifts.local",
        "password": "WrongPassword123"
    })
    assert response2.status_code == 200
    assert b"Invalid email or password" in response2.data

def test_login_post_inactive_user(client, app):
    """Ensure POST /login with a disabled user account fails."""
    # First, deactivate the admin user
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET active = 0 WHERE username = 'admin@meatheadlifts.local'")
        conn.commit()
        conn.close()

    response = client.post("/login", data={
        "email": "admin@meatheadlifts.local",
        "password": "ChangeMe123"
    })
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data

def test_login_post_valid_credentials(client):
    """Ensure POST /login with valid email and password redirects to /."""
    response = client.post("/login", data={
        "email": "admin@meatheadlifts.local",
        "password": "ChangeMe123"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

def test_login_post_safe_next_url(client):
    """Ensure POST /login with valid credentials and a safe next URL redirects properly."""
    response = client.post("/login?next=/admin", data={
        "email": "admin@meatheadlifts.local",
        "password": "ChangeMe123"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/admin"


def test_login_post_unsafe_next_url(client):
    """Ensure POST /login with valid credentials and an unsafe next URL redirects to /."""
    response = client.post("/login?next=http://malicious.com", data={
        "email": "admin@meatheadlifts.local",
        "password": "ChangeMe123"
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/"
