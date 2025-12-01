# CI-CD-python-project

## Membres du groupe
- AMBRY Lukas
- CARK Dryss
- RONDEAU Allan

---

## 1. Repository GitHub Public
**URL du repository:** `https://github.com/Lukasambry/CI-CD-python-project`

---

## 2. Captures d'écran

# A remplir

---

## 3. Fichiers Créés

### 3.1 Application Flask - `app.py`

```python
import sqlite3
import os
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
DATABASE = 'users.db'


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ('admin', 'admin@example.com', 'admin123'),
            ('user1', 'user1@example.com', 'password1'),
            ('user2', 'user2@example.com', 'password2')
        ]
        cursor.executemany('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', sample_users)

    conn.commit()
    conn.close()


@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to the Best API ever created by mankind !!!!!! (or not)',
        'endpoints': {
            '/': 'This help message',
            '/user/<username>': 'Get user by username (SQL Injection vulnerable)',
            '/file': 'Download file (Path Traversal vulnerable)',
            '/health': 'Health check endpoint'
        }
    })


@app.route('/user/<username>')
def get_user(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    query = f"SELECT username, email FROM users WHERE username = '{username}'"
    cursor.execute(query)

    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            'username': user[0],
            'email': user[1]
        })
    return jsonify({'error': 'User not found'}), 404


@app.route('/file')
def download_file():
    filename = request.args.get('name', 'default.txt')

    try:
        return send_file(filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200


def add_user(username, email, password):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                   (username, email, password))
    conn.commit()
    conn.close()
    return True


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 3.2 Dépendances - `requirements.txt`

```txt
Flask==2.3.0
Werkzeug==2.3.0
pytest==7.4.0
flake8==6.0.0
```

### 3.3 Tests Pytest - `tests/test_app.py`

```python
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
```

### 3.4 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["python", "app.py"]
```

### 3.5 CI Workflow - `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches:
      - main
      - master
  workflow_dispatch:

permissions:
  contents: read
  security-events: write
  actions: read

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10']

    steps:
      - name: checkout
        uses: actions/checkout@v5

      - name: Python ${{ matrix.python-version }}
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}

      - name: dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install flake8 pytest

      - name: flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --statistics

      - name: pytest
        run: |
          pytest tests/

  trivy-scan:
    runs-on: ubuntu-latest

    steps:
      - name: checkout
        uses: actions/checkout@v5

      - name: trivy FS mode
        uses: aquasecurity/trivy-action@0.33.1
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: upload
        uses: github/codeql-action/upload-sarif@v4
        with:
          sarif_file: 'results.sarif'
```

### 3.6 CD Workflow - `.github/workflows/cd.yml`

```yaml
name: CD

on:
  workflow_run:
    workflows: ["CI"]
    types:
      - completed

jobs:
  build:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}

    steps:
      - name: checkout
        uses: actions/checkout@v5

      - name: login
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: build and push
        uses: docker/build-push-action@v6
        id: push
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ secrets.DOCKER_USERNAME }}/ci-cd-python-app:latest
```