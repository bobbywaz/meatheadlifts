import os
import tempfile
import pytest
from pathlib import Path

import app

@pytest.fixture
def client(monkeypatch):
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setattr(app, 'DB_PATH', Path(db_path))

    app.app.config['TESTING'] = True

    with app.app.test_client() as client:
        with app.app.app_context():
            app.init_db()
        yield client

    os.close(db_fd)
    os.unlink(db_path)
