import sqlite3
import bcrypt
import os

DB_PATH = 'classified.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            cipher TEXT DEFAULT 'caesar',
            shift INTEGER DEFAULT 3,
            keyword TEXT DEFAULT 'KEY',
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            is_encrypted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def create_user(username, password):
    conn = get_db()
    c = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                  (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
        return dict(user)
    return None

def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def create_room(name, created_by, cipher='caesar', shift=3, keyword='KEY'):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO rooms (name, created_by, cipher, shift, keyword)
                     VALUES (?, ?, ?, ?, ?)''',
                  (name, created_by, cipher, shift, keyword))
        conn.commit()
        room_id = c.lastrowid
        conn.close()
        return room_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_all_rooms():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT rooms.*, users.username as creator
                 FROM rooms LEFT JOIN users ON rooms.created_by = users.id
                 ORDER BY rooms.created_at DESC''')
    rooms = [dict(r) for r in c.fetchall()]
    conn.close()
    return rooms

def get_room(room_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
    room = c.fetchone()
    conn.close()
    return dict(room) if room else None

def save_message(room_id, user_id, username, content, is_encrypted=False):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO messages (room_id, user_id, username, content, is_encrypted)
                 VALUES (?, ?, ?, ?, ?)''',
              (room_id, user_id, username, content, int(is_encrypted)))
    conn.commit()
    conn.close()

def get_messages(room_id, limit=50):
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT * FROM messages WHERE room_id = ?
                 ORDER BY created_at ASC LIMIT ?''', (room_id, limit))
    messages = [dict(m) for m in c.fetchall()]
    conn.close()
    return messages