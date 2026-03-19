import os
import tempfile
from pathlib import Path

import pytest

import app as flask_app_module
from app import app as flask_app
from app import get_db, init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    old_db_path = flask_app_module.DB_PATH
    flask_app_module.DB_PATH = Path(db_path)

    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",
    })

    # Initialize the database
    with flask_app.app_context():
        init_db()

    yield flask_app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    flask_app_module.DB_PATH = old_db_path


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def db_conn(app):
    # This fixture yields a database connection.
    # It must be used within the app context.
    conn = get_db()
    yield conn
    conn.close()
