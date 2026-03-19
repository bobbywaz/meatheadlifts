import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
import pytest
from app import app, init_db, get_db
import app as app_module

@pytest.fixture
def client():
    # Set up a temporary database
    db_fd, db_path = tempfile.mkstemp()
    app_module.DB_PATH = app_module.Path(db_path)

    app.config["TESTING"] = True

    with app.app_context():
        init_db()

    with app.test_client() as client:
        yield client

    # Teardown
    os.close(db_fd)
    os.unlink(db_path)

def test_api_history_unauthorized(client):
    # Call without login
    response = client.get("/api/history")
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}

def test_api_history_empty(client):
    # Log in first
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # admin user created in init_db

    response = client.get("/api/history")
    assert response.status_code == 200
    assert response.get_json() == []

def test_api_history_success(client):
    # Log in
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    # Insert mock data directly
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()

        # Insert 25 sessions
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        for i in range(25):
            workout_type = "A" if i % 2 == 0 else "B"
            completed_at = (base_time + timedelta(days=i)).isoformat()
            started_at = (base_time + timedelta(days=i, hours=-1)).isoformat()

            cur.execute(
                """
                INSERT INTO workout_sessions (workout_type, started_at, completed_at)
                VALUES (?, ?, ?)
                """,
                (workout_type, started_at, completed_at)
            )
        conn.commit()
        conn.close()

    response = client.get("/api/history")
    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)

    # Should only return 20 items (LIMIT 20)
    assert len(data) == 20

    # Check ordering (descending)
    # The first item should be the most recently completed one (i=24)
    assert data[0]["workout"] == "A"  # 24 % 2 == 0 -> A
    assert data[0]["completed_at"] == (base_time + timedelta(days=24)).isoformat()
    assert data[0]["id"] == 25

    # Check structure
    assert "id" in data[0]
    assert "workout" in data[0]
    assert "completed_at" in data[0]
    assert "workout_type" not in data[0] # Should be mapped to 'workout'
