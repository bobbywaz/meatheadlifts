def test_api_history_session_not_found(client):
    """Test retrieving a non-existent session ID via API."""
    # Log in using the default admin created in init_db
    client.post('/login', data={
        'email': 'admin@meatheadlifts.local',
        'password': 'ChangeMe123'
    })

    # Request a non-existent session ID
    response = client.get('/api/history/9999')

    # Assert correct response for missing session
    assert response.status_code == 404
    assert response.get_json() == {"error": "Workout session not found"}
