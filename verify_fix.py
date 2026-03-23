import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from unittest.mock import MagicMock, patch

# Mock Flask components for testing since they are not installed
import sys
from types import ModuleType

mock_flask = ModuleType("flask")
mock_flask.Flask = MagicMock()
mock_flask.flash = MagicMock()
mock_flask.g = MagicMock()
mock_flask.jsonify = MagicMock()
mock_flask.redirect = MagicMock()
mock_flask.render_template = MagicMock()
mock_flask.request = MagicMock()
mock_flask.send_from_directory = MagicMock()
mock_flask.session = {}
mock_flask.url_for = MagicMock()
sys.modules["flask"] = mock_flask

# Import the code to test
import app

DB_FILE = "test_meatheadlifts.db"

def setup_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    app.DB_PATH = os.path.abspath(DB_FILE)
    app.init_db()

def test_init_db_no_env():
    print("Testing init_db without environment variables...")
    os.environ.pop("INITIAL_ADMIN_USERNAME", None)
    os.environ.pop("INITIAL_ADMIN_PASSWORD", None)
    setup_db()

    conn = sqlite3.connect(DB_FILE)
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()

    assert count == 0, f"Expected 0 users, found {count}"
    print("SUCCESS: No users created when env vars are missing.")

def test_init_db_with_env():
    print("Testing init_db with environment variables...")
    os.environ["INITIAL_ADMIN_USERNAME"] = "testadmin@example.com"
    os.environ["INITIAL_ADMIN_PASSWORD"] = "TestPassword123"
    setup_db()

    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT username FROM users").fetchone()
    assert row is not None, "Admin user should have been created"
    assert row[0] == "testadmin@example.com", f"Expected testadmin@example.com, found {row[0]}"

    # Check admin group
    is_admin = conn.execute("""
        SELECT EXISTS(
            SELECT 1 FROM user_permission_groups upg
            JOIN permission_groups pg ON pg.id = upg.group_id
            JOIN users u ON u.id = upg.user_id
            WHERE u.username = 'testadmin@example.com' AND pg.name = 'admin'
        )
    """).fetchone()[0]
    assert is_admin == 1, "User should be in admin group"

    conn.close()
    print("SUCCESS: Admin user created with env vars.")

def test_signup_promotes_first_user():
    print("Testing signup promotes first user to admin...")
    os.environ.pop("INITIAL_ADMIN_USERNAME", None)
    os.environ.pop("INITIAL_ADMIN_PASSWORD", None)
    setup_db()

    # Mock request.form for signup
    app.request.form = {
        "email": "first@example.com",
        "password": "Password123",
        "confirm_password": "Password123"
    }
    app.g.current_user = None

    # Call signup
    with patch('app.render_signup_page') as mock_render:
        app.signup()

    conn = sqlite3.connect(DB_FILE)
    row = conn.execute("SELECT username FROM users WHERE username = 'first@example.com'").fetchone()
    assert row is not None, "User should have been created"

    # Check admin group
    is_admin = conn.execute("""
        SELECT EXISTS(
            SELECT 1 FROM user_permission_groups upg
            JOIN permission_groups pg ON pg.id = upg.group_id
            JOIN users u ON u.id = upg.user_id
            WHERE u.username = 'first@example.com' AND pg.name = 'admin'
        )
    """).fetchone()[0]
    assert is_admin == 1, "First user should be an admin"

    # Sign up a second user
    app.request.form = {
        "email": "second@example.com",
        "password": "Password123",
        "confirm_password": "Password123"
    }
    with patch('app.render_signup_page') as mock_render:
        app.signup()

    is_admin_2 = conn.execute("""
        SELECT EXISTS(
            SELECT 1 FROM user_permission_groups upg
            JOIN permission_groups pg ON pg.id = upg.group_id
            JOIN users u ON u.id = upg.user_id
            WHERE u.username = 'second@example.com' AND pg.name = 'admin'
        )
    """).fetchone()[0]
    assert is_admin_2 == 0, "Second user should NOT be an admin"

    conn.close()
    print("SUCCESS: First user promoted to admin, second user not.")

if __name__ == "__main__":
    try:
        test_init_db_no_env()
        test_init_db_with_env()
        test_signup_promotes_first_user()
        print("\nAll tests passed successfully!")
    finally:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
