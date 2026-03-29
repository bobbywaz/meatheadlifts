import pytest

def test_api_history_unauthenticated(client):
    """Test that an unauthenticated request returns a 401 error."""
    response = client.get('/api/history')
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Unauthorized"

def test_api_history_empty(auth_client):
    """Test that an authenticated request with no history returns an empty list."""
    response = auth_client.get('/api/history')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_api_history_populated(auth_client):
    """Test that an authenticated request returns history when populated."""
    # Pre-populate with a workout
    payload_a = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    complete_response = auth_client.post('/api/complete', json=payload_a)
    assert complete_response.status_code == 200

    response = auth_client.get('/api/history')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()

    assert isinstance(data, list)
    assert len(data) == 1

    workout = data[0]
    assert "id" in workout
    assert workout["workout"] == "A"
    assert "completed_at" in workout

def test_api_history_ordering(auth_client):
    """Test that history returns most recent workouts first."""
    # Workout 1
    payload_a = {
        "workout": "A",
        "exercises": [
            {"name": "Squat", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Bench Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Barbell Row", "weight": 45, "sets": [5, 5, 5, 5, 5]}
        ]
    }
    auth_client.post('/api/complete', json=payload_a)

    # Workout 2
    payload_b = {
        "workout": "B",
        "exercises": [
            {"name": "Squat", "weight": 50, "sets": [5, 5, 5, 5, 5]},
            {"name": "Overhead Press", "weight": 45, "sets": [5, 5, 5, 5, 5]},
            {"name": "Deadlift", "weight": 95, "sets": [5]}
        ]
    }
    auth_client.post('/api/complete', json=payload_b)

    response = auth_client.get('/api/history')
    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 2
    assert data[0]["workout"] == "B"
    assert data[1]["workout"] == "A"

    # Check that data[0] is strictly newer or equal to data[1]
    assert data[0]["completed_at"] >= data[1]["completed_at"]
