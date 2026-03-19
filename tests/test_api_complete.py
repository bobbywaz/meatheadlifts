def test_api_complete_invalid_payload(auth_client):
    """Test that an invalid payload returns a 400 error."""
    # Send a request without the required 'workout' field
    response = auth_client.post('/api/complete', json={"invalid": "payload"})

    assert response.status_code == 400
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid workout type"

def test_api_complete_invalid_exercise(auth_client):
    """Test that an invalid exercise payload returns a 400 error."""
    payload = {
        "workout": "A",
        "exercises": [
            {
                "name": "Squat",
                "weight": "not a number",
                "sets": [5, 5, 5, 5, 5]
            }
        ]
    }
    response = auth_client.post('/api/complete', json=payload)

    assert response.status_code == 400
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    # The actual error message from validate_workout_payload:
    # "Exercises do not match workout" because the other exercises are missing.
    assert "Exercises do not match workout" in data["error"]

def test_api_complete_invalid_weight(auth_client):
    """Test that an invalid weight returns a 400 error."""
    payload = {
        "workout": "A",
        "exercises": [
            {
                "name": "Squat",
                "weight": "not a number",
                "sets": [5, 5, 5, 5, 5]
            },
            {
                "name": "Bench Press",
                "weight": 45,
                "sets": [5, 5, 5, 5, 5]
            },
            {
                "name": "Barbell Row",
                "weight": 45,
                "sets": [5, 5, 5, 5, 5]
            }
        ]
    }
    response = auth_client.post('/api/complete', json=payload)

    assert response.status_code == 400
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid weight for Squat"
