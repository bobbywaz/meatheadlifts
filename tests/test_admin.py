import os
import tempfile
import pytest
from pathlib import Path

# Add the project root to the path so we can import app
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app as myapp

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()

    myapp.app.config['TESTING'] = True
    myapp.app.config['WTF_CSRF_ENABLED'] = False

    # Save the original DB_PATH
    original_db_path = myapp.DB_PATH

    # Change DB_PATH to use our temp file
    myapp.DB_PATH = Path(db_path)

    # Initialize the database with the temp file
    myapp.init_db()

    with myapp.app.test_client() as client:
        with myapp.app.app_context():
            yield client

    # Restore original DB_PATH
    myapp.DB_PATH = original_db_path

    os.close(db_fd)
    os.unlink(db_path)

def test_admin_create_user_existing_email(client):
    # Log in as admin
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # admin user created in init_db

    # Create a test user first
    response = client.post(
        '/admin/users',
        data={
            'email': 'testuser@example.com',
            'password': 'Password123!',
            'is_admin': '0'
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"User created: testuser@example.com" in response.data

    # Try to create another user with the exact same email
    response = client.post(
        '/admin/users',
        data={
            'email': 'testuser@example.com',
            'password': 'AnotherPassword123!',
            'is_admin': '0'
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"An account with that email already exists" in response.data

    # Try to create another user with a different case email (but same address)
    # email validation handles lowercase conversions
    response = client.post(
        '/admin/users',
        data={
            'email': 'TESTUSER@example.com',
            'password': 'AnotherPassword123!',
            'is_admin': '0'
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"An account with that email already exists" in response.data
