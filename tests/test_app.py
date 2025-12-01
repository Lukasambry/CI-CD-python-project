import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, init_db, add_user, DATABASE


@pytest.fixture
def client():
    app.config['TESTING'] = True

    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    init_db()

    with app.test_client() as client:
        yield client

    if os.path.exists(DATABASE):
        os.remove(DATABASE)


def test_home_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'endpoints' in data


def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_get_user_exists(client):
    response = client.get('/user/admin')
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'admin'
    assert 'email' in data


def test_get_user_not_exists(client):
    response = client.get('/user/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_add_user():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    init_db()
    result = add_user('testuser', 'test@example.com', 'testpass')
    assert result is True

    if os.path.exists(DATABASE):
        os.remove(DATABASE)


def test_file_endpoint_missing_param(client):
    response = client.get('/file')
    assert response.status_code in [200, 400]


def test_multiple_users(client):
    users = ['admin', 'user1', 'user2']
    for username in users:
        response = client.get(f'/user/{username}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['username'] == username
