import os
import tempfile
import pytest
from app import app, init_db, get_db
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True

    # Mock the DB_PATH in app.py
    import app as myapp
    from pathlib import Path
    myapp.DB_PATH = Path(db_path)

    with app.test_client() as client:
        with app.app_context():
            init_db()

            # Create some test users
            conn = get_db()
            cur = conn.cursor()
            now = "2023-01-01T00:00:00"

            # Clear default users first
            cur.execute("DELETE FROM users")
            cur.execute("DELETE FROM user_permission_groups")

            # User 1: Admin 1
            cur.execute(
                "INSERT INTO users (id, username, password_hash, active, created_at) VALUES (?, ?, ?, ?, ?)",
                (1, "admin1", generate_password_hash("pass"), 1, now)
            )
            # User 2: Admin 2
            cur.execute(
                "INSERT INTO users (id, username, password_hash, active, created_at) VALUES (?, ?, ?, ?, ?)",
                (2, "admin2", generate_password_hash("pass"), 1, now)
            )
            # User 3: Normal User
            cur.execute(
                "INSERT INTO users (id, username, password_hash, active, created_at) VALUES (?, ?, ?, ?, ?)",
                (3, "normal", generate_password_hash("pass"), 1, now)
            )

            # Get admin group id
            admin_group_id = cur.execute("SELECT id FROM permission_groups WHERE name = 'admin'").fetchone()["id"]

            # Assign admin privileges
            cur.execute("INSERT INTO user_permission_groups (user_id, group_id) VALUES (?, ?)", (1, admin_group_id))
            cur.execute("INSERT INTO user_permission_groups (user_id, group_id) VALUES (?, ?)", (2, admin_group_id))

            conn.commit()

        yield client

    os.close(db_fd)
    os.unlink(db_path)

def login(client, username, password):
    return client.post('/login', data=dict(
        email=username,
        password=password
    ), follow_redirects=True)

def test_admin_delete_normal_user(client):
    """Test that an admin can delete a normal user."""
    # Login as admin1
    login(client, 'admin1', 'pass')

    # Try to delete normal user (id=3)
    response = client.post('/admin/users/3/delete', follow_redirects=True)
    assert response.status_code == 200

    # Verify user is deleted
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = 3").fetchone()
        assert user is None

def test_admin_delete_self(client):
    """Test that an admin cannot delete themselves."""
    # Login as admin1
    login(client, 'admin1', 'pass')

    # Try to delete self (id=1)
    response = client.post('/admin/users/1/delete', follow_redirects=True)
    assert response.status_code == 200

    # Verify user is NOT deleted
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
        assert user is not None

def test_admin_delete_another_admin(client):
    """Test that an admin can delete another admin if there are multiple admins."""
    # Login as admin1
    login(client, 'admin1', 'pass')

    # Try to delete admin2 (id=2)
    response = client.post('/admin/users/2/delete', follow_redirects=True)
    assert response.status_code == 200

    # Verify admin2 is deleted
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = 2").fetchone()
        assert user is None

def test_admin_delete_last_admin(client):
    """Test that the last admin cannot be deleted."""
    # Login as admin1
    login(client, 'admin1', 'pass')

    # First, delete admin2 so admin1 is the only admin
    response = client.post('/admin/users/2/delete', follow_redirects=True)
    assert response.status_code == 200

    # Verify admin2 is deleted and admin count is 1
    with app.app_context():
        conn = get_db()
        admin_count = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM users u
            WHERE EXISTS(
              SELECT 1
              FROM user_permission_groups upg
              JOIN permission_groups pg ON pg.id = upg.group_id
              WHERE upg.user_id = u.id AND pg.name = 'admin'
            )
            """
        ).fetchone()["count"]
        assert admin_count == 1

    # To test the admin_count <= 1 branch directly, we bypass the view wrapper
    # and call admin_delete_user, manipulating g directly in a test_request_context
    from app import admin_delete_user
    from flask import g

    with app.test_request_context('/admin/users/1/delete', method='POST'):
        # Set g.current_user to pretend we are a different user (e.g. id=999)
        # This bypasses the `if user_id == g.current_user["id"]` check
        g.current_user = {"id": 999, "is_admin": True}

        # Call the view function
        response = admin_delete_user(1)

        # Verify it returns a redirect (status code 302 to admin_page)
        assert response.status_code == 302

        # Verify admin1 is NOT deleted from the database
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
        assert user is not None
