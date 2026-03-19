import os
import tempfile
from pathlib import Path
import pytest

import app as my_app

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    # Override the DB_PATH for testing
    my_app.DB_PATH = Path(db_path)

    my_app.app.config['TESTING'] = True

    with my_app.app.test_client() as client:
        with my_app.app.app_context():
            my_app.init_db()
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_api_state_unauthorized(client):
    response = client.get('/api/state')
    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}

def test_api_state_authorized(client):
    # Log in
    login_resp = client.post('/login', data={
        'email': 'admin@meatheadlifts.local',
        'password': 'ChangeMe123'
    })
    assert login_resp.status_code in (200, 302)

    # Get state
    response = client.get('/api/state')
    assert response.status_code == 200

    data = response.json
    assert data is not None
    assert 'workout' in data
    assert 'exercises' in data

    assert data['workout'] == 'A'

    exercises = data['exercises']
    assert len(exercises) == 3

    ex_names = [ex['name'] for ex in exercises]
    assert ex_names == ["Squat", "Bench Press", "Barbell Row"]

    for ex in exercises:
        assert 'weight' in ex
        assert 'sets' in ex
        assert 'notes' in ex
        assert ex['notes'] == ''
        assert ex['sets'] == [5, 5, 5, 5, 5]
