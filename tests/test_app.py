import pytest

from app import get_user_by_username, get_db, validate_workout_payload


def test_init_db(app, db_conn):
    """Test that the database is initialized correctly."""
    # Test that tables exist
    tables = db_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [row["name"] for row in tables]
    expected_tables = [
        "profile", "exercise_weights", "workout_sessions",
        "session_sets", "session_exercise_notes", "users",
        "permission_groups", "user_permission_groups"
    ]
    for table in expected_tables:
        assert table in table_names

    # Test initial admin user exists
    user = get_user_by_username(db_conn, "admin@meatheadlifts.local")
    assert user is not None
    assert user["active"] == 1

    # Test default weights are inserted
    weights = db_conn.execute("SELECT exercise_name, weight FROM exercise_weights").fetchall()
    weight_map = {row["exercise_name"]: row["weight"] for row in weights}
    assert weight_map.get("Squat") == 45
    assert weight_map.get("Deadlift") == 95

    # Test profile exists with default workout A
    profile = db_conn.execute("SELECT next_workout FROM profile WHERE id = 1").fetchone()
    assert profile is not None
    assert profile["next_workout"] == "A"


def test_validate_workout_payload():
    # Valid payload A
    payload_a = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 100, "sets": [5, 5, 5, 5, 5], "notes": "Felt good"},
            {"name": "Bench Press", "weight": 100, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 100, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    w_type, exercises, err = validate_workout_payload(payload_a)
    assert err is None
    assert w_type == "A"
    assert len(exercises) == 3
    assert exercises[0]["notes"] == "Felt good"
    assert exercises[1]["notes"] == ""

    # Invalid workout type
    payload_invalid = {"workout": "C", "exercises": []}
    w_type, exercises, err = validate_workout_payload(payload_invalid)
    assert err == "Invalid workout type"

    # Missing exercise
    payload_missing = {
        "workout": "B",
        "exercises": [
            {"name": "Squat", "weight": 100, "sets": [5, 5, 5, 5, 5]},
            {"name": "Deadlift", "weight": 100, "sets": [5]}
        ]
    }
    w_type, exercises, err = validate_workout_payload(payload_missing)
    assert err == "Exercises do not match workout"

    # Invalid rep count (e.g., 6 sets for Squat instead of 5)
    payload_bad_sets = {
        "workout": "B",
        "exercises": [
            {"name": "Squat", "weight": 100, "sets": [5, 5, 5, 5, 5, 5]},
            {"name": "Overhead Press", "weight": 100, "sets": [5, 5, 5, 5, 5]},
            {"name": "Deadlift", "weight": 100, "sets": [5]}
        ]
    }
    w_type, exercises, err = validate_workout_payload(payload_bad_sets)
    assert err == "Unexpected set count for Squat"


def test_api_complete_and_history(client, app, db_conn):
    # First login
    with app.app_context():
        response = client.post("/login", data={
            "email": "admin@meatheadlifts.local",
            "password": "ChangeMe123"
        }, follow_redirects=True)
        assert response.status_code == 200

        # Check API state
        response = client.get("/api/state")
        assert response.status_code == 200
        state = response.get_json()
        assert state["workout"] == "A"

        # Complete a workout
        payload = {
            "workout": "A",
            "exercises": [
                {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": "First workout"},
                {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""},
                {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""}
            ]
        }
        response = client.post("/api/complete", json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert data["next_workout"] == "B"

        # Check that it's in the history
        response = client.get("/api/history")
        assert response.status_code == 200
        history = response.get_json()
        assert len(history) == 1
        assert history[0]["workout"] == "A"
        session_id = history[0]["id"]

        # Check history details
        response = client.get(f"/api/history/{session_id}")
        assert response.status_code == 200
        details = response.get_json()
        assert details["workout"] == "A"
        assert details["notes"].get("Squat") == "First workout"
        assert len(details["sets"]) == 15  # 3 exercises * 5 sets

        # Update history session
        payload_update = {
            "workout": "A",
            "exercises": [
                {"name": "Squat", "weight": 50, "sets": [5, 5, 5, 5, 5], "notes": "Updated weight"},
                {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""},
                {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5], "notes": ""}
            ]
        }
        response = client.put(f"/api/history/{session_id}", json=payload_update)
        assert response.status_code == 200

        # Verify update
        response = client.get(f"/api/history/{session_id}")
        details = response.get_json()
        assert details["sets"][0]["weight"] == 50
        assert details["notes"].get("Squat") == "Updated weight"

        # Delete history session
        response = client.delete(f"/api/history/{session_id}")
        assert response.status_code == 200

        # Verify deletion
        response = client.get("/api/history")
        history = response.get_json()
        assert len(history) == 0


def test_admin_routes(client, app):
    # Try accessing admin without login
    response = client.get("/admin")
    assert response.status_code == 302

    # Login as normal user (need to create one first)
    with app.app_context():
        client.post("/signup", data={
            "email": "normal@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!"
        })
        client.post("/login", data={
            "email": "normal@example.com",
            "password": "Password123!"
        }, follow_redirects=True)

        # Try accessing admin as normal user
        response = client.get("/admin")
        assert response.status_code == 302
        assert response.headers["Location"] == "/"  # Should redirect to index

        # Try accessing api admin route as normal user
        response = client.get("/api/admin/users")
        assert response.status_code == 403

        # Logout
        client.post("/logout")

        # Login as admin
        client.post("/login", data={
            "email": "admin@meatheadlifts.local",
            "password": "ChangeMe123"
        }, follow_redirects=True)

        # Access admin page
        response = client.get("/admin")
        assert response.status_code == 200

        # Access api admin route
        response = client.get("/api/admin/users")
        assert response.status_code == 200
        users = response.get_json()
        assert len(users) >= 1
