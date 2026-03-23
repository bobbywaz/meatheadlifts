import os
import tempfile
import pytest
from app import app, init_db, get_db

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'

    # Overwrite DB_PATH in app to use temporary DB
    from app import DB_PATH
    import app as app_module
    app_module.DB_PATH = type(DB_PATH)(db_path)

    os.environ['INITIAL_ADMIN_USERNAME'] = 'admin@meatheadlifts.local'
    os.environ['INITIAL_ADMIN_PASSWORD'] = 'ChangeMe123'

    with app.app_context():
        init_db()

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_api_admin_users_unauthorized(client):
    response = client.get('/api/admin/users')
    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}

def test_api_admin_users_forbidden(client):
    # Register a regular user
    response = client.post('/signup', data={
        'email': 'user@test.com',
        'password': 'TestPassword123!',
        'confirm_password': 'TestPassword123!'
    })
    assert response.status_code == 200

    # Log in as the regular user
    response = client.post('/login', data={
        'email': 'user@test.com',
        'password': 'TestPassword123!'
    })
    assert response.status_code == 302 # Redirect after login

    # Try to access admin endpoint
    response = client.get('/api/admin/users')
    assert response.status_code == 403
    assert response.json == {"error": "Forbidden"}

def test_api_admin_users_success(client):
    # Register a regular user to have at least two users
    client.post('/signup', data={
        'email': 'user@test.com',
        'password': 'TestPassword123!',
        'confirm_password': 'TestPassword123!'
    })

    # Log in as the admin user created by init_db
    response = client.post('/login', data={
        'email': 'admin@meatheadlifts.local',
        'password': 'ChangeMe123'
    })
    assert response.status_code == 302 # Redirect after successful login

    # Access the admin users endpoint
    response = client.get('/api/admin/users')
    assert response.status_code == 200

    users = response.json
    assert isinstance(users, list)
    assert len(users) >= 2

    admin_user = next((u for u in users if u['username'] == 'admin@meatheadlifts.local'), None)
    regular_user = next((u for u in users if u['username'] == 'user@test.com'), None)

    assert admin_user is not None
    assert admin_user['is_admin'] is True
    assert admin_user['active'] is True

    assert regular_user is not None
    assert regular_user['is_admin'] is False
    assert regular_user['active'] is True
