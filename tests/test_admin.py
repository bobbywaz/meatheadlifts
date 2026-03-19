import pytest

def test_admin_create_user_invalid_email(client):
    # Log in as admin
    login_res = client.post('/login', data={
        'email': 'admin@meatheadlifts.local',
        'password': 'ChangeMe123'
    }, follow_redirects=True)
    assert login_res.status_code == 200

    # Try to create user with an invalid email
    response = client.post('/admin/users', data={
        'email': 'invalid-email-format',
        'password': 'ValidPassword123',
        'is_admin': ''
    }, follow_redirects=False)

    # The view should redirect back to the admin page
    assert response.status_code == 302
    assert response.headers['Location'] == '/admin'

    # Follow the redirect to check for flash error message
    follow_up = client.get(response.headers['Location'])
    assert b'Invalid email format' in follow_up.data
