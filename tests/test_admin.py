import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
from werkzeug.security import generate_password_hash

import app
from app import app as flask_app, init_db, get_db

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.DB_PATH = Path(db_path)

    flask_app.config['TESTING'] = True
    flask_app.secret_key = 'test'

    with flask_app.app_context():
        init_db()

    with flask_app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_admin_delete_user_last_admin(client):
    # Log in as initial admin (id=1)
    client.post('/login', data={'email': 'admin@meatheadlifts.local', 'password': 'ChangeMe123'})

    # Create a dummy admin in the mock to test the `admin_count <= 1` branch
    # while bypassing the self-deletion check. The reviewer pointed out that
    # mocking `app.g` is an anti-pattern. Mucking with `app.get_user_by_id`
    # is cleaner because `get_user_by_id` is a standard helper method.
    with patch('app.get_user_by_id') as mock_get_user:
        mock_get_user.return_value = {
            "id": 999,
            "username": "other_admin@meatheadlifts.local",
            "is_admin": True
        }

        # User ID 1 is the ONLY admin in the DB.
        rv = client.post('/admin/users/1/delete')
        assert rv.status_code == 302

        # Verify the only admin was NOT deleted
        conn = get_db()
        user1 = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
        conn.close()
        assert user1 is not None

def test_admin_delete_user_not_last_admin(client):
    client.post('/login', data={'email': 'admin@meatheadlifts.local', 'password': 'ChangeMe123'})

    conn = get_db()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO users (username, password_hash, active, created_at) VALUES (?, ?, 1, ?)",
        ("admin2@meatheadlifts.local", generate_password_hash("ChangeMe123"), now)
    )
    admin2_id = cur.lastrowid
    group_id = cur.execute("SELECT id FROM permission_groups WHERE name = 'admin'").fetchone()["id"]
    cur.execute(
        "INSERT INTO user_permission_groups (user_id, group_id) VALUES (?, ?)",
        (admin2_id, group_id)
    )
    conn.commit()
    conn.close()

    rv = client.post(f'/admin/users/{admin2_id}/delete')
    assert rv.status_code == 302

    conn = get_db()
    user2 = conn.execute("SELECT * FROM users WHERE id = ?", (admin2_id,)).fetchone()
    conn.close()
    assert user2 is None

def test_admin_delete_self(client):
    client.post('/login', data={'email': 'admin@meatheadlifts.local', 'password': 'ChangeMe123'})
    rv = client.post('/admin/users/1/delete')
    assert rv.status_code == 302

    conn = get_db()
    user1 = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
    conn.close()
    assert user1 is not None

def test_admin_delete_non_existent(client):
    client.post('/login', data={'email': 'admin@meatheadlifts.local', 'password': 'ChangeMe123'})
    rv = client.post('/admin/users/999/delete')
    assert rv.status_code == 302

def test_admin_delete_user_is_not_admin(client):
    client.post('/login', data={'email': 'admin@meatheadlifts.local', 'password': 'ChangeMe123'})

    conn = get_db()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute(
        "INSERT INTO users (username, password_hash, active, created_at) VALUES (?, ?, 1, ?)",
        ("normal@meatheadlifts.local", generate_password_hash("ChangeMe123"), now)
    )
    normal_id = cur.lastrowid
    conn.commit()
    conn.close()

    rv = client.post(f'/admin/users/{normal_id}/delete')
    assert rv.status_code == 302

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (normal_id,)).fetchone()
    conn.close()
    assert user is None
