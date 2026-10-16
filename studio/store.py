"""Durable, single-worker queue. Interrupted jobs require an explicit retry."""
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager


class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, created REAL, updated REAL, state TEXT,
                progress INTEGER, phase TEXT, spec TEXT, error TEXT, output TEXT, verification TEXT)''')
            db.execute("UPDATE jobs SET state='interrupted', phase='Stopped before completion', error='Studio restarted. Submit a new job to retry.' WHERE state IN ('running','cancelling')")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, spec):
        job_id = uuid.uuid4().hex
        now = time.time()
        with self.connect() as db:
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)',
                       (job_id, now, now, 'queued', 0, 'Waiting', json.dumps(spec), '', '', '{}'))
        return self.get(job_id)

    @staticmethod
    def decode(row):
        if row is None:
            return None
        item = dict(row)
        item['spec'] = json.loads(item['spec'])
        item['verification'] = json.loads(item['verification'])
        item.pop('output')
        item['download'] = '/api/jobs/' + item['id'] + '/video' if item['state'] == 'succeeded' else None
        return item

    def get(self, job_id):
        with self.connect() as db:
            return self.decode(db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone())

    def list(self):
        with self.connect() as db:
            return [self.decode(r) for r in db.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 100')]

    def claim(self):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT id FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
            if row:
                db.execute("UPDATE jobs SET state='running', phase='Preparing', updated=? WHERE id=?", (time.time(), row['id']))
        return self.get(row['id']) if row else None

    def update(self, job_id, **fields):
        allowed = {'state', 'progress', 'phase', 'error', 'output', 'verification'}
        if not set(fields) <= allowed:
            raise ValueError('Invalid queue field')
        if 'verification' in fields:
            fields['verification'] = json.dumps(fields['verification'])
        fields['updated'] = time.time()
        with self.connect() as db:
            db.execute('UPDATE jobs SET ' + ','.join(k + '=?' for k in fields) + ' WHERE id=?', (*fields.values(), job_id))

    def cancel(self, job_id):
        with self.connect() as db:
            db.execute("UPDATE jobs SET state=CASE WHEN state='queued' THEN 'cancelled' ELSE 'cancelling' END, phase='Cancellation requested' WHERE id=? AND state IN ('queued','running')", (job_id,))
        return self.get(job_id)

    def output(self, job_id):
        with self.connect() as db:
            row = db.execute("SELECT output FROM jobs WHERE id=? AND state='succeeded'", (job_id,)).fetchone()
            return row['output'] if row else None
