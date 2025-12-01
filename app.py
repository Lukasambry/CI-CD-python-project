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
