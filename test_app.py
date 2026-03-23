import os
import tempfile
import pytest
from app import app, init_db, get_db

@pytest.fixture
def test_db():
    db_fd, db_path = tempfile.mkstemp()
    app.config["TESTING"] = True

    # We patch the DB_PATH within app module directly
    # But get_db creates connection to app.DB_PATH
    import app as app_module
    from pathlib import Path
    old_db_path = app_module.DB_PATH
    app_module.DB_PATH = Path(db_path)

    with app.app_context():
        init_db()

    yield

    os.close(db_fd)
    os.unlink(db_path)
    app_module.DB_PATH = old_db_path

@pytest.fixture
def client(test_db):
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_client(client):
    # Log in as the default admin user created in init_db
    client.post('/login', data={'email': 'admin@meatheadlifts.local', 'password': 'ChangeMe123'})
    yield client

def test_api_update_history_session_success(auth_client):
    # 1. Seed a session
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": "Felt good"},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""}
        ]
    }

    res = auth_client.post('/api/complete', json=payload)
    assert res.status_code == 200

    # Verify session is created and get its ID
    res = auth_client.get('/api/history')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    session_id = data[0]['id']

    # 2. Update the session (changing workout to B, different exercises/weights)
    update_payload = {
        "workout": "B",
        "exercises": [
            {"name": "Squat", "weight": 55, "sets": [5, 5, 5, 5, 5], "notes": "Increased weight"},
            {"name": "Overhead Press", "weight": 45, "sets": [5, 5, 5, 5, 4], "notes": "Missed last rep"},
            {"name": "Deadlift", "weight": 95, "sets": [5], "notes": "Solid"}
        ]
    }

    res = auth_client.put(f'/api/history/{session_id}', json=update_payload)
    assert res.status_code == 200
    assert res.get_json()['status'] == 'ok'

    # 3. Verify changes were correctly saved
    res = auth_client.get(f'/api/history/{session_id}')
    assert res.status_code == 200
    data = res.get_json()

    assert data['id'] == session_id
    assert data['workout'] == "B"

    # sets
    assert len(data['sets']) == 11 # 5 + 5 + 1

    # Find Overhead Press specific sets
    ohp_sets = [s for s in data['sets'] if s['exercise_name'] == 'Overhead Press']
    assert len(ohp_sets) == 5
    assert ohp_sets[-1]['completed_reps'] == 4 # The last set we missed a rep

    # Check squat weight
    squat_sets = [s for s in data['sets'] if s['exercise_name'] == 'Squat']
    assert squat_sets[0]['weight'] == 55

    # notes
    notes = data['notes']
    assert notes.get("Squat") == "Increased weight"
    assert notes.get("Overhead Press") == "Missed last rep"
    assert notes.get("Deadlift") == "Solid"
    assert "Bench Press" not in notes # Should be deleted since we updated from A to B

def test_api_update_history_session_not_found(auth_client):
    update_payload = {
        "workout": "B",
        "exercises": [
            {"name": "Squat", "weight": 55, "sets": [5, 5, 5, 5, 5], "notes": ""},
            {"name": "Overhead Press", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""},
            {"name": "Deadlift", "weight": 95, "sets": [5], "notes": ""}
        ]
    }
    res = auth_client.put('/api/history/999', json=update_payload)
    assert res.status_code == 404
    assert res.get_json()['error'] == "Workout session not found"

def test_api_update_history_session_invalid_payload(auth_client):
    # Seed a session
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""}
        ]
    }

    res = auth_client.post('/api/complete', json=payload)
    session_id = auth_client.get('/api/history').get_json()[0]['id']

    # Update with invalid payload (missing exercises)
    update_payload = {
        "workout": "B",
        "exercises": [
            {"name": "Squat", "weight": 55, "sets": [5, 5, 5, 5, 5], "notes": ""}
        ]
    }

    res = auth_client.put(f'/api/history/{session_id}', json=update_payload)
    assert res.status_code == 400
    assert res.get_json()['error'] == "Exercises do not match workout"

def test_api_update_history_session_unauthenticated(client):
    # Attempting to PUT without auth should fail
    res = client.put('/api/history/1', json={})
    assert res.status_code == 401
    assert res.get_json()['error'] == "Unauthorized"
