import os
import tempfile
import pytest

from app import app as flask_app, init_db, get_db


@pytest.fixture
def app():
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()

    flask_app.config.update(
        {
            "TESTING": True,
        }
    )

    # Override the DB path for testing
    from pathlib import Path
    import app as app_module

    app_module.DB_PATH = Path(db_path)

    # Set test environment variables to avoid randomly generated passwords
    os.environ["INITIAL_ADMIN_USERNAME"] = "admin@meatheadlifts.local"
    os.environ["INITIAL_ADMIN_PASSWORD"] = "ChangeMe123"

    # Initialize the database
    with flask_app.app_context():
        init_db()

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client, app):
    # Log in as the default admin user created in init_db
    with client:
        client.post(
            "/login",
            data={"email": "admin@meatheadlifts.local", "password": "ChangeMe123"},
        )
        yield client
