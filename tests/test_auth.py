import pytest
from app import validate_email, validate_password, get_user_by_username


def test_validate_email():
    # Valid emails
    email, err = validate_email("test@example.com")
    assert email == "test@example.com"
    assert err is None

    email, err = validate_email("  TEST@example.com  ")
    assert email == "test@example.com"
    assert err is None

    # Invalid emails
    email, err = validate_email("")
    assert email is None
    assert err == "Email is required"

    email, err = validate_email("invalid-email")
    assert email is None
    assert err == "Invalid email format"

    email, err = validate_email("test@")
    assert email is None
    assert err == "Invalid email format"

    email, err = validate_email("@example.com")
    assert email is None
    assert err == "Invalid email format"


def test_validate_password():
    # Valid password
    err = validate_password("Password123!")
    assert err is None

    # Invalid passwords
    err = validate_password("short")
    assert err == "Password must be at least 8 characters"

    err = validate_password("ALLUPPERCASE123")
    assert err == "Password must include a lowercase letter"

    err = validate_password("alllowercase123")
    assert err == "Password must include an uppercase letter"

    err = validate_password("NoNumbersHere")
    assert err == "Password must include a number"


def test_signup(client, db_conn):
    # Test successful signup
    response = client.post("/signup", data={
        "email": "newuser@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert response.status_code == 200
    assert b"Account created. You can now sign in." in response.data

    user = get_user_by_username(db_conn, "newuser@example.com")
    assert user is not None
    assert user["active"] == 1

    # Test duplicate username
    response = client.post("/signup", data={
        "email": "newuser@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert response.status_code == 200
    assert b"An account with that email already exists" in response.data

    # Test password mismatch
    response = client.post("/signup", data={
        "email": "anotheruser@example.com",
        "password": "Password123!",
        "confirm_password": "WrongPassword123!"
    })
    assert response.status_code == 200
    assert b"Passwords do not match" in response.data


def test_login_logout(client, app):
    # Use the admin account created in init_db
    with app.app_context():
        response = client.post("/login", data={
            "email": "admin@meatheadlifts.local",
            "password": "ChangeMe123"
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to index and we should be logged in
        assert b"admin@meatheadlifts.local" in response.data or b"Logout" in response.data

        # Test logout
        response = client.post("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data

    # Test invalid login
    response = client.post("/login", data={
        "email": "admin@meatheadlifts.local",
        "password": "wrongpassword"
    })
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_protected_routes(client):
    # Accessing protected route without login should redirect
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"] in ("/login?next=%2F", "/login?next=/")

    response = client.get("/admin")
    assert response.status_code == 302
    assert response.headers["Location"] in ("/login?next=%2Fadmin", "/login?next=/admin")

    # API endpoints should return 401
    response = client.get("/api/state")
    assert response.status_code == 401
