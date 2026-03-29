def test_api_update_history_invalid_payload(auth_client):
    """Test that an invalid payload returns a 400 error when updating a history session."""
    # Send a PUT request without the required 'workout' field
    response = auth_client.put('/api/history/1', json={"invalid": "payload"})

    assert response.status_code == 400
    assert response.is_json

    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid workout type"
