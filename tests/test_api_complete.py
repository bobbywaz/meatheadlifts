import pytest
import app

def test_api_complete_unauthorized(client):
    response = client.post("/api/complete", json={})
    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}

def test_api_complete_invalid_payload(auth_client):
    response = auth_client.post("/api/complete", json={"workout": "C"})
    assert response.status_code == 400
    assert "error" in response.json
    assert response.json["error"] == "Invalid workout type"

def test_api_complete_missing_exercises(auth_client):
    response = auth_client.post("/api/complete", json={"workout": "A"})
    assert response.status_code == 400
    assert response.json["error"] == "Exercises do not match workout"

def test_api_complete_happy_path_workout_a(auth_client):
    payload = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": "Felt good"},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }

    response = auth_client.post("/api/complete", json=payload)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["next_workout"] == "B"

    # Verify database side effects
    with auth_client.application.app_context():
        conn = app.get_db()

        # 1. Check workout_sessions
        session_row = conn.execute("SELECT * FROM workout_sessions ORDER BY id DESC LIMIT 1").fetchone()
        assert session_row is not None
        assert session_row["workout_type"] == "A"
        session_id = session_row["id"]

        # 2. Check session_sets (5 sets * 3 exercises = 15 rows)
        sets_count = conn.execute("SELECT COUNT(*) FROM session_sets WHERE session_id = ?", (session_id,)).fetchone()[0]
        assert sets_count == 15

        # 3. Check exercise_weights
        squat_weight = conn.execute("SELECT weight FROM exercise_weights WHERE exercise_name = 'Squat'").fetchone()[0]
        assert squat_weight == 45.0

        # 4. Check session_exercise_notes
        squat_note = conn.execute("SELECT notes FROM session_exercise_notes WHERE session_id = ? AND exercise_name = 'Squat'", (session_id,)).fetchone()[0]
        assert squat_note == "Felt good"

        # 5. Check next_workout in profile table
        next_workout = conn.execute("SELECT next_workout FROM profile WHERE id = 1").fetchone()[0]
        assert next_workout == "B"

        conn.close()

def test_api_complete_happy_path_workout_b(auth_client):
    # Setup: insert a previous Workout A to test switching from B back to A
    with auth_client.application.app_context():
        conn = app.get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO workout_sessions (workout_type, started_at, completed_at) VALUES ('A', '2023-01-01T00:00:00', '2023-01-01T01:00:00')")
        cur.execute("UPDATE profile SET next_workout = 'B' WHERE id = 1")
        conn.commit()
        conn.close()

    payload = {
        "workout": "B",
        "exercises": [
            {"name": "Squat", "weight": 50, "sets": [5, 5, 5, 5, 5]},
            {"name": "Overhead Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Deadlift", "weight": 95, "sets": [5]}  # Deadlift only expects 1 set
        ]
    }

    response = auth_client.post("/api/complete", json=payload)
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["next_workout"] == "A"

    # Verify Deadlift sets
    with auth_client.application.app_context():
        conn = app.get_db()
        session_row = conn.execute("SELECT * FROM workout_sessions ORDER BY id DESC LIMIT 1").fetchone()
        session_id = session_row["id"]

        dl_sets_count = conn.execute("SELECT COUNT(*) FROM session_sets WHERE session_id = ? AND exercise_name = 'Deadlift'", (session_id,)).fetchone()[0]
        assert dl_sets_count == 1

        conn.close()
