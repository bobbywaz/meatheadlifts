import os
import tempfile
from pathlib import Path
import pytest

import app as myapp
from app import app as flask_app

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret"
    })

    # Override database path for tests
    original_db_path = myapp.DB_PATH
    myapp.DB_PATH = Path(db_path)

    with flask_app.app_context():
        myapp.init_db()

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)
    myapp.DB_PATH = original_db_path

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
