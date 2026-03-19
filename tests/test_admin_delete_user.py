import os
import sqlite3
import tempfile
import pytest

from app import app, init_db, get_db
import app as app_module

@pytest.fixture
def client():
    # Create a temporary file to act as the sqlite database
    db_fd, db_path = tempfile.mkstemp()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    # Mock the DB_PATH in the app module
    import pathlib
    original_db_path = app_module.DB_PATH
    app_module.DB_PATH = pathlib.Path(db_path)

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    app_module.DB_PATH = original_db_path

def test_admin_cannot_delete_self(client):
    # Log in as the default admin
    response = client.post("/login", data={
        "email": "admin@meatheadlifts.local",
        "password": "ChangeMe123"
    }, follow_redirects=True)
    assert b"admin@meatheadlifts.local" in response.data or response.status_code == 200

    # Try to delete self
    # Assuming default admin has id=1
    response = client.post("/admin/users/1/delete", follow_redirects=False)

    # Should redirect back to admin page
    assert response.status_code == 302
    assert response.headers["Location"] == "/admin"

    # Verify the admin user is still in the database
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
        conn.close()

    assert user is not None
    assert user["username"] == "admin@meatheadlifts.local"

def test_admin_can_delete_other_user(client):
    # Log in as the default admin
    client.post("/login", data={
        "email": "admin@meatheadlifts.local",
        "password": "ChangeMe123"
    }, follow_redirects=True)

    # Create another user
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        from werkzeug.security import generate_password_hash
        cur.execute(
            """
            INSERT INTO users (username, password_hash, active, created_at)
            VALUES (?, ?, 1, ?)
            """,
            ("other@meatheadlifts.local", generate_password_hash("test"), "2023-01-01T00:00:00")
        )
        other_user_id = cur.lastrowid
        conn.commit()
        conn.close()

    # Try to delete the other user
    response = client.post(f"/admin/users/{other_user_id}/delete", follow_redirects=False)

    # Should redirect back to admin page
    assert response.status_code == 302
    assert response.headers["Location"] == "/admin"

    # Verify the other user is deleted
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (other_user_id,)).fetchone()
        conn.close()

    assert user is None
