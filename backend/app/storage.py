import json
import sqlite3
from contextlib import contextmanager


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'interviews.sqlite3'
        with self.connection() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL, document TEXT NOT NULL)''')

    @contextmanager
    def connection(self):
        with sqlite3.connect(self.path, timeout=10) as db:
            db.row_factory = sqlite3.Row
            yield db

    def save(self, session):
        with self.connection() as db:
            db.execute('''INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET status=excluded.status, document=excluded.document''',
                       (session['id'], session['name'], session['role'], session['status'],
                        session['created_at'], json.dumps(session)))

    def get(self, session_id):
        with self.connection() as db:
            row = db.execute('SELECT document FROM sessions WHERE id=?', (session_id,)).fetchone()
        return json.loads(row['document']) if row else None

    def list(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute(
                'SELECT id,name,role,status,created_at FROM sessions ORDER BY created_at DESC LIMIT 50')]
