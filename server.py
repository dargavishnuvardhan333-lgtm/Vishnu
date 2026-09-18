from flask import Flask, render_template_string, request, redirect, jsonify, session
from datetime import datetime
import sqlite3
import re

app = Flask(__name__)
app.secret_key = 'local-admin-session-key'
DB_NAME = 'messages.db'
ADMIN_PASSWORD = 'manu@2004'

with open('index.html', 'r', encoding='utf-8') as f:
    page_html = f.read()

with open('admin.html', 'r', encoding='utf-8') as f:
    admin_html = f.read()

with open('admin_login.html', 'r', encoding='utf-8') as f:
    admin_login_html = f.read()


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()

    columns = [row['name'] for row in conn.execute('PRAGMA table_info(messages)').fetchall()]
    if 'phone' not in columns:
        conn.execute('ALTER TABLE messages ADD COLUMN phone TEXT')
        conn.commit()
    conn.close()


init_db()


@app.route('/')
def home():
    return render_template_string(page_html)


@app.route('/admin')
def admin():
    if not session.get('admin_authenticated'):
        return render_template_string(admin_login_html)
    return render_template_string(admin_html)


@app.route('/admin/login', methods=['POST'])
def admin_login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['admin_authenticated'] = True
        return redirect('/admin')

    return render_template_string(admin_login_html, error='Incorrect password.'), 401


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect('/admin')


@app.route('/api/messages')
def get_messages():
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Admin login required'}), 401

    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM messages ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/submit', methods=['POST'])
def submit_form():
    name = request.form.get('name')
    phone = request.form.get('phone', '').strip()
    message = request.form.get('message')

    if not name or not phone or not message:
        return redirect('/?error=missing')

    digits = re.sub(r'\D', '', phone)
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]

    if not re.fullmatch(r'[6-9]\d{9}', digits):
        return redirect('/?error=phone')

    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO messages (name, email, phone, message, created_at) VALUES (?, ?, ?, ?, ?)',
        (name, '', digits, message, created_at)
    )
    conn.commit()
    conn.close()

    print(f"Saved to database: {name} ({phone})")
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
