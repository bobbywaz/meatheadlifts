import os
import tempfile
from pathlib import Path

import pytest
from flask import session

# Patch the DB_PATH before importing app so it picks up the patched version,
# though we can also patch it after importing.
import app


@pytest.fixture
def test_app(tmp_path):
    # Override the app's database path
    original_db_path = app.DB_PATH
    db_path = tmp_path / "test.db"
    app.DB_PATH = db_path

    # Configure the app for testing
    app.app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
    })

    # Initialize the database schema and seed data within an app context
    with app.app.app_context():
        app.init_db()

    yield app.app

    # Clean up
    app.DB_PATH = original_db_path


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def runner(test_app):
    return test_app.test_cli_runner()


@pytest.fixture
def auth_client(client, test_app):
    """A test client that is logged in as the admin user."""
    # Seed user is created in init_db(): admin@meatheadlifts.local / ChangeMe123
    response = client.post(
        "/login",
        data={
            "email": "admin@meatheadlifts.local",
            "password": "ChangeMe123"
        }
    )
    assert response.status_code == 302 # Redirect to index
    return client
